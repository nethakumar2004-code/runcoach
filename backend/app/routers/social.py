from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import timedelta

from app.db import get_db
from app.models.user import User
from app.models.run import CompletedRun
from app.models.social import (
    Friendship, ActivityFeed, ActivityLike, ActivityComment,
    Challenge, ChallengeParticipant, Kudos
)
from app.schemas.social import (
    FriendRequest, FriendshipResponse, FriendsList,
    ActivityResponse, ActivityComment as ActivityCommentSchema,
    ActivityCommentResponse, ChallengeCreate, ChallengeResponse,
    KudosResponse, KudosToggleResponse, LeaderboardEntry, WeeklyLeaderboard, SocialStats
)
from app.dependencies import get_current_user
from app.services.social import are_friends, get_friend_ids, refresh_participation
from app.timeutils import utcnow

router = APIRouter()


def _visible_activity(db: Session, activity_id: str, user: User) -> ActivityFeed:
    """An activity the user may see: their own, or a friend's public one."""
    activity = db.query(ActivityFeed).filter(ActivityFeed.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if activity.user_id != user.id and not (activity.is_public and are_friends(db, user.id, activity.user_id)):
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


def _friendship_response(friendship: Friendship, other: User) -> FriendshipResponse:
    return FriendshipResponse(
        id=friendship.id,
        requester_id=friendship.requester_id,
        addressee_id=friendship.addressee_id,
        status=friendship.status,
        created_at=friendship.created_at,
        friend_name=other.name,
        friend_email=other.email
    )


# Friends Management
@router.post("/friends/request", response_model=dict)
def send_friend_request(
    request: FriendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_user = db.query(User).filter(func.lower(User.email) == request.email.strip().lower()).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")

    existing = db.query(Friendship).filter(
        or_(
            and_(Friendship.requester_id == current_user.id, Friendship.addressee_id == target_user.id),
            and_(Friendship.requester_id == target_user.id, Friendship.addressee_id == current_user.id)
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Friendship request already exists")

    db.add(Friendship(
        requester_id=current_user.id,
        addressee_id=target_user.id,
        status="pending"
    ))
    db.commit()

    return {"message": f"Friend request sent to {target_user.name or target_user.email}"}

@router.post("/friends/{friendship_id}/accept", response_model=dict)
def accept_friend_request(
    friendship_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    friendship = db.query(Friendship).filter(
        Friendship.id == friendship_id,
        Friendship.addressee_id == current_user.id,
        Friendship.status == "pending"
    ).first()
    if not friendship:
        raise HTTPException(status_code=404, detail="Friend request not found")

    friendship.status = "accepted"
    db.commit()

    return {"message": "Friend request accepted"}

@router.get("/friends", response_model=FriendsList)
def get_friends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # The old query selected (Friendship, User) without a join, so every friend appeared once per user in the app
    friendships = db.query(Friendship).filter(
        Friendship.status == "accepted",
        or_(
            Friendship.requester_id == current_user.id,
            Friendship.addressee_id == current_user.id
        )
    ).all()
    other_ids = [f.addressee_id if f.requester_id == current_user.id else f.requester_id for f in friendships]
    users_by_id = {u.id: u for u in db.query(User).filter(User.id.in_(other_ids)).all()} if other_ids else {}

    friends = []
    for friendship, other_id in zip(friendships, other_ids):
        if other_id in users_by_id:
            friends.append(_friendship_response(friendship, users_by_id[other_id]))

    pending_requests = [
        _friendship_response(friendship, requester)
        for friendship, requester in db.query(Friendship, User).join(
            User, Friendship.requester_id == User.id
        ).filter(
            Friendship.addressee_id == current_user.id,
            Friendship.status == "pending"
        ).all()
    ]

    sent_requests = [
        _friendship_response(friendship, addressee)
        for friendship, addressee in db.query(Friendship, User).join(
            User, Friendship.addressee_id == User.id
        ).filter(
            Friendship.requester_id == current_user.id,
            Friendship.status == "pending"
        ).all()
    ]

    return FriendsList(
        friends=friends,
        pending_requests=pending_requests,
        sent_requests=sent_requests
    )

# Activity Feed
@router.get("/feed", response_model=List[ActivityResponse])
def get_activity_feed(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    friend_ids = get_friend_ids(db, current_user.id)

    # Your own activities, plus your friends' public ones
    activities = db.query(ActivityFeed, User).join(
        User, ActivityFeed.user_id == User.id
    ).filter(
        or_(
            ActivityFeed.user_id == current_user.id,
            and_(ActivityFeed.user_id.in_(friend_ids), ActivityFeed.is_public == True)
        )
    ).order_by(desc(ActivityFeed.created_at)).limit(limit).all()

    # Count likes/comments for the whole page in 3 queries instead of 3 per activity
    ids = [activity.id for activity, _ in activities]
    likes = dict(db.query(ActivityLike.activity_id, func.count()).filter(
        ActivityLike.activity_id.in_(ids)).group_by(ActivityLike.activity_id).all()) if ids else {}
    comments = dict(db.query(ActivityComment.activity_id, func.count()).filter(
        ActivityComment.activity_id.in_(ids)).group_by(ActivityComment.activity_id).all()) if ids else {}
    liked = {a_id for (a_id,) in db.query(ActivityLike.activity_id).filter(
        ActivityLike.activity_id.in_(ids), ActivityLike.user_id == current_user.id)} if ids else set()

    return [
        ActivityResponse(
            id=activity.id,
            user_id=activity.user_id,
            user_name=user.name,
            activity_type=activity.activity_type,
            activity_data=activity.activity_data,
            created_at=activity.created_at,
            likes_count=likes.get(activity.id, 0),
            comments_count=comments.get(activity.id, 0),
            user_liked=activity.id in liked
        )
        for activity, user in activities
    ]

@router.post("/activities/{activity_id}/like", response_model=dict)
def toggle_activity_like(
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _visible_activity(db, activity_id, current_user)

    existing_like = db.query(ActivityLike).filter(
        ActivityLike.activity_id == activity_id,
        ActivityLike.user_id == current_user.id
    ).first()

    if existing_like:
        db.delete(existing_like)
        db.commit()
        return {"message": "Activity unliked", "liked": False}

    db.add(ActivityLike(activity_id=activity_id, user_id=current_user.id))
    db.commit()
    return {"message": "Activity liked", "liked": True}

@router.get("/activities/{activity_id}/comments", response_model=List[ActivityCommentResponse])
def get_activity_comments(
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _visible_activity(db, activity_id, current_user)
    rows = db.query(ActivityComment, User).join(User, ActivityComment.user_id == User.id).filter(
        ActivityComment.activity_id == activity_id
    ).order_by(ActivityComment.created_at).all()
    return [
        ActivityCommentResponse(
            id=comment.id, user_id=comment.user_id, user_name=user.name,
            comment_text=comment.comment_text, created_at=comment.created_at
        )
        for comment, user in rows
    ]

@router.post("/activities/{activity_id}/comments", response_model=ActivityCommentResponse)
def add_activity_comment(
    activity_id: str,
    comment: ActivityCommentSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _visible_activity(db, activity_id, current_user)
    new_comment = ActivityComment(
        activity_id=activity_id, user_id=current_user.id, comment_text=comment.comment_text.strip()
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return ActivityCommentResponse(
        id=new_comment.id, user_id=current_user.id, user_name=current_user.name,
        comment_text=new_comment.comment_text, created_at=new_comment.created_at
    )

# Kudos
def _visible_run(db: Session, run_id: str, user: User) -> CompletedRun:
    run = db.query(CompletedRun).filter(CompletedRun.id == run_id).first()
    if not run or (run.user_id != user.id and not are_friends(db, user.id, run.user_id)):
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@router.post("/runs/{run_id}/kudos", response_model=KudosToggleResponse)
def toggle_kudos(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    run = _visible_run(db, run_id, current_user)
    if run.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You can't give kudos to your own run")

    existing = db.query(Kudos).filter(Kudos.run_id == run_id, Kudos.giver_id == current_user.id).first()
    if existing:
        db.delete(existing)
        given = False
    else:
        db.add(Kudos(run_id=run_id, giver_id=current_user.id, receiver_id=run.user_id))
        given = True
    db.commit()

    return KudosToggleResponse(
        run_id=run_id,
        given=given,
        kudos_count=db.query(Kudos).filter(Kudos.run_id == run_id).count()
    )

@router.get("/runs/{run_id}/kudos", response_model=List[KudosResponse])
def get_kudos(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _visible_run(db, run_id, current_user)
    rows = db.query(Kudos, User).join(User, Kudos.giver_id == User.id).filter(
        Kudos.run_id == run_id
    ).order_by(Kudos.created_at).all()
    return [
        KudosResponse(id=k.id, giver_id=k.giver_id, giver_name=giver.name, created_at=k.created_at)
        for k, giver in rows
    ]

# Challenges
def _challenge_response(db: Session, challenge: Challenge, creator_name, current_user: User) -> ChallengeResponse:
    participants_count = db.query(ChallengeParticipant).filter(
        ChallengeParticipant.challenge_id == challenge.id
    ).count()
    participation = db.query(ChallengeParticipant).filter(
        ChallengeParticipant.challenge_id == challenge.id,
        ChallengeParticipant.user_id == current_user.id
    ).first()
    return ChallengeResponse(
        id=challenge.id,
        name=challenge.name,
        description=challenge.description,
        challenge_type=challenge.challenge_type,
        target_value=challenge.target_value,
        start_date=challenge.start_date,
        end_date=challenge.end_date,
        created_by=challenge.created_by,
        creator_name=creator_name,
        is_public=challenge.is_public,
        participants_count=participants_count,
        user_participating=participation is not None,
        user_progress=participation.current_progress if participation else 0,
        user_completed=participation.completed if participation else False
    )

@router.post("/challenges", response_model=ChallengeResponse)
def create_challenge(
    challenge: ChallengeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_challenge = Challenge(
        name=challenge.name,
        description=challenge.description,
        challenge_type=challenge.challenge_type,
        target_value=challenge.target_value,
        start_date=challenge.start_date,
        end_date=challenge.end_date,
        created_by=current_user.id,
        is_public=challenge.is_public
    )
    db.add(new_challenge)
    db.flush()

    # Auto-join the creator; runs already inside the challenge window count straight away
    participant = ChallengeParticipant(challenge_id=new_challenge.id, user_id=current_user.id)
    db.add(participant)
    refresh_participation(db, participant, new_challenge)
    db.commit()

    return _challenge_response(db, new_challenge, current_user.name, current_user)

@router.get("/challenges", response_model=List[ChallengeResponse])
def get_challenges(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Challenge, User).join(User, Challenge.created_by == User.id)

    if active_only:
        now = utcnow()
        query = query.filter(Challenge.start_date <= now, Challenge.end_date >= now)

    # Public challenges, plus private ones the user created or joined
    joined_ids = db.query(ChallengeParticipant.challenge_id).filter(
        ChallengeParticipant.user_id == current_user.id
    )
    query = query.filter(or_(
        Challenge.is_public == True,
        Challenge.created_by == current_user.id,
        Challenge.id.in_(joined_ids),
    ))
    challenges = query.order_by(desc(Challenge.created_at)).all()

    return [_challenge_response(db, challenge, creator.name, current_user) for challenge, creator in challenges]

@router.post("/challenges/{challenge_id}/join", response_model=dict)
def join_challenge(
    challenge_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge or (not challenge.is_public and challenge.created_by != current_user.id):
        raise HTTPException(status_code=404, detail="Challenge not found")

    now = utcnow()
    if now < challenge.start_date or now > challenge.end_date:
        raise HTTPException(status_code=400, detail="Challenge is not active")

    existing = db.query(ChallengeParticipant).filter(
        ChallengeParticipant.challenge_id == challenge_id,
        ChallengeParticipant.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already participating in this challenge")

    participant = ChallengeParticipant(challenge_id=challenge_id, user_id=current_user.id)
    db.add(participant)
    refresh_participation(db, participant, challenge)
    db.commit()

    return {"message": f"Joined challenge: {challenge.name}"}

# Leaderboards
@router.get("/leaderboard/weekly", response_model=WeeklyLeaderboard)
def get_weekly_leaderboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = utcnow()
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)

    member_ids = get_friend_ids(db, current_user.id) + [current_user.id]

    weekly_stats = db.query(
        CompletedRun.user_id,
        User.name,
        func.sum(CompletedRun.distance_km).label('total_distance'),
        func.count(CompletedRun.id).label('total_runs'),
        func.sum(CompletedRun.duration_sec).label('total_time'),
    ).join(User, CompletedRun.user_id == User.id).filter(
        CompletedRun.user_id.in_(member_ids),
        CompletedRun.start_datetime >= week_start,
        CompletedRun.start_datetime < week_end
    ).group_by(CompletedRun.user_id, User.name).all()

    entries = [
        LeaderboardEntry(
            user_id=row.user_id,
            user_name=row.name,
            total_distance=float(row.total_distance or 0),
            total_runs=row.total_runs,
            # Total time / total distance, so a short fast run doesn't outweigh a long one
            avg_pace=float(row.total_time / row.total_distance) if row.total_distance else 0.0,
            rank=0
        )
        for row in weekly_stats
    ]

    entries.sort(key=lambda x: x.total_distance, reverse=True)
    for i, entry in enumerate(entries):
        entry.rank = i + 1

    return WeeklyLeaderboard(
        week_start=week_start,
        week_end=week_end,
        entries=entries
    )

@router.get("/stats", response_model=SocialStats)
def get_social_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = utcnow()
    return SocialStats(
        friends_count=len(get_friend_ids(db, current_user.id)),
        activities_count=db.query(ActivityFeed).filter(ActivityFeed.user_id == current_user.id).count(),
        kudos_received=db.query(Kudos).filter(Kudos.receiver_id == current_user.id).count(),
        kudos_given=db.query(Kudos).filter(Kudos.giver_id == current_user.id).count(),
        challenges_completed=db.query(ChallengeParticipant).filter(
            ChallengeParticipant.user_id == current_user.id,
            ChallengeParticipant.completed == True
        ).count(),
        current_challenges=db.query(ChallengeParticipant).join(
            Challenge, ChallengeParticipant.challenge_id == Challenge.id
        ).filter(
            ChallengeParticipant.user_id == current_user.id,
            Challenge.start_date <= now,
            Challenge.end_date >= now,
            ChallengeParticipant.completed == False
        ).count()
    )
