from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta

from app.db import get_db
from app.models.user import User
from app.models.run import CompletedRun
from app.models.social import (
    Friendship, ActivityFeed, ActivityLike, ActivityComment, 
    Challenge, ChallengeParticipant, Kudos
)
from app.schemas.social import (
    FriendRequest, FriendshipResponse, FriendsList,
    ActivityCreate, ActivityResponse, ActivityComment as ActivityCommentSchema,
    ActivityCommentResponse, ChallengeCreate, ChallengeResponse,
    ChallengeLeaderboard, ChallengeParticipantResponse,
    KudosResponse, LeaderboardEntry, WeeklyLeaderboard, SocialStats
)
from app.dependencies import get_current_user

router = APIRouter()

# Friends Management
@router.post("/friends/request", response_model=dict)
def send_friend_request(
    request: FriendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find user by email
    target_user = db.query(User).filter(User.email == request.email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")
    
    # Check if friendship already exists
    existing = db.query(Friendship).filter(
        or_(
            and_(Friendship.requester_id == current_user.id, Friendship.addressee_id == target_user.id),
            and_(Friendship.requester_id == target_user.id, Friendship.addressee_id == current_user.id)
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Friendship request already exists")
    
    # Create friendship request
    friendship = Friendship(
        requester_id=current_user.id,
        addressee_id=target_user.id,
        status="pending"
    )
    db.add(friendship)
    db.commit()
    
    return {"message": f"Friend request sent to {target_user.name}"}

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
    # Get accepted friendships
    friends_query = db.query(Friendship, User).filter(
        Friendship.status == "accepted"
    ).filter(
        or_(
            Friendship.requester_id == current_user.id,
            Friendship.addressee_id == current_user.id
        )
    )
    
    friends = []
    for friendship, _ in friends_query.all():
        friend_id = friendship.addressee_id if friendship.requester_id == current_user.id else friendship.requester_id
        friend = db.query(User).filter(User.id == friend_id).first()
        
        friends.append(FriendshipResponse(
            id=friendship.id,
            requester_id=friendship.requester_id,
            addressee_id=friendship.addressee_id,
            status=friendship.status,
            created_at=friendship.created_at,
            friend_name=friend.name,
            friend_email=friend.email
        ))
    
    # Get pending requests (received)
    pending_requests = []
    pending_query = db.query(Friendship, User).join(
        User, Friendship.requester_id == User.id
    ).filter(
        Friendship.addressee_id == current_user.id,
        Friendship.status == "pending"
    )
    
    for friendship, requester in pending_query.all():
        pending_requests.append(FriendshipResponse(
            id=friendship.id,
            requester_id=friendship.requester_id,
            addressee_id=friendship.addressee_id,
            status=friendship.status,
            created_at=friendship.created_at,
            friend_name=requester.name,
            friend_email=requester.email
        ))
    
    # Get sent requests
    sent_requests = []
    sent_query = db.query(Friendship, User).join(
        User, Friendship.addressee_id == User.id
    ).filter(
        Friendship.requester_id == current_user.id,
        Friendship.status == "pending"
    )
    
    for friendship, addressee in sent_query.all():
        sent_requests.append(FriendshipResponse(
            id=friendship.id,
            requester_id=friendship.requester_id,
            addressee_id=friendship.addressee_id,
            status=friendship.status,
            created_at=friendship.created_at,
            friend_name=addressee.name,
            friend_email=addressee.email
        ))
    
    return FriendsList(
        friends=friends,
        pending_requests=pending_requests,
        sent_requests=sent_requests
    )

# Activity Feed
@router.get("/feed", response_model=List[ActivityResponse])
def get_activity_feed(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Get friend IDs
    friend_ids = []
    friendships = db.query(Friendship).filter(
        or_(
            Friendship.requester_id == current_user.id,
            Friendship.addressee_id == current_user.id
        ),
        Friendship.status == "accepted"
    ).all()
    
    for friendship in friendships:
        friend_id = friendship.addressee_id if friendship.requester_id == current_user.id else friendship.requester_id
        friend_ids.append(friend_id)
    
    # Include current user's activities
    friend_ids.append(current_user.id)
    
    # Get activities from friends and self
    activities = db.query(ActivityFeed, User).join(
        User, ActivityFeed.user_id == User.id
    ).filter(
        ActivityFeed.user_id.in_(friend_ids),
        ActivityFeed.is_public == True
    ).order_by(desc(ActivityFeed.created_at)).limit(limit).all()
    
    result = []
    for activity, user in activities:
        # Count likes and comments
        likes_count = db.query(ActivityLike).filter(ActivityLike.activity_id == activity.id).count()
        comments_count = db.query(ActivityComment).filter(ActivityComment.activity_id == activity.id).count()
        
        # Check if current user liked this activity
        user_liked = db.query(ActivityLike).filter(
            ActivityLike.activity_id == activity.id,
            ActivityLike.user_id == current_user.id
        ).first() is not None
        
        result.append(ActivityResponse(
            id=activity.id,
            user_id=activity.user_id,
            user_name=user.name,
            activity_type=activity.activity_type,
            activity_data=activity.activity_data,
            created_at=activity.created_at,
            likes_count=likes_count,
            comments_count=comments_count,
            user_liked=user_liked
        ))
    
    return result

@router.post("/activities/{activity_id}/like", response_model=dict)
def toggle_activity_like(
    activity_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if activity exists
    activity = db.query(ActivityFeed).filter(ActivityFeed.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Check if user already liked this activity
    existing_like = db.query(ActivityLike).filter(
        ActivityLike.activity_id == activity_id,
        ActivityLike.user_id == current_user.id
    ).first()
    
    if existing_like:
        # Unlike
        db.delete(existing_like)
        db.commit()
        return {"message": "Activity unliked", "liked": False}
    else:
        # Like
        like = ActivityLike(
            activity_id=activity_id,
            user_id=current_user.id
        )
        db.add(like)
        db.commit()
        return {"message": "Activity liked", "liked": True}

# Challenges
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
    db.commit()
    db.refresh(new_challenge)
    
    # Auto-join creator to challenge
    participant = ChallengeParticipant(
        challenge_id=new_challenge.id,
        user_id=current_user.id
    )
    db.add(participant)
    db.commit()
    
    return ChallengeResponse(
        id=new_challenge.id,
        name=new_challenge.name,
        description=new_challenge.description,
        challenge_type=new_challenge.challenge_type,
        target_value=new_challenge.target_value,
        start_date=new_challenge.start_date,
        end_date=new_challenge.end_date,
        created_by=new_challenge.created_by,
        creator_name=current_user.name,
        is_public=new_challenge.is_public,
        participants_count=1,
        user_participating=True,
        user_progress=0,
        user_completed=False
    )

@router.get("/challenges", response_model=List[ChallengeResponse])
def get_challenges(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Challenge, User).join(User, Challenge.created_by == User.id)
    
    if active_only:
        now = datetime.utcnow()
        query = query.filter(
            Challenge.start_date <= now,
            Challenge.end_date >= now
        )
    
    query = query.filter(Challenge.is_public == True)
    challenges = query.order_by(desc(Challenge.created_at)).all()
    
    result = []
    for challenge, creator in challenges:
        # Count participants
        participants_count = db.query(ChallengeParticipant).filter(
            ChallengeParticipant.challenge_id == challenge.id
        ).count()
        
        # Check if current user is participating
        user_participation = db.query(ChallengeParticipant).filter(
            ChallengeParticipant.challenge_id == challenge.id,
            ChallengeParticipant.user_id == current_user.id
        ).first()
        
        result.append(ChallengeResponse(
            id=challenge.id,
            name=challenge.name,
            description=challenge.description,
            challenge_type=challenge.challenge_type,
            target_value=challenge.target_value,
            start_date=challenge.start_date,
            end_date=challenge.end_date,
            created_by=challenge.created_by,
            creator_name=creator.name,
            is_public=challenge.is_public,
            participants_count=participants_count,
            user_participating=user_participation is not None,
            user_progress=user_participation.current_progress if user_participation else 0,
            user_completed=user_participation.completed if user_participation else False
        ))
    
    return result

@router.post("/challenges/{challenge_id}/join", response_model=dict)
def join_challenge(
    challenge_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if challenge exists and is active
    challenge = db.query(Challenge).filter(Challenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    now = datetime.utcnow()
    if now < challenge.start_date or now > challenge.end_date:
        raise HTTPException(status_code=400, detail="Challenge is not active")
    
    # Check if user is already participating
    existing = db.query(ChallengeParticipant).filter(
        ChallengeParticipant.challenge_id == challenge_id,
        ChallengeParticipant.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already participating in this challenge")
    
    # Join challenge
    participant = ChallengeParticipant(
        challenge_id=challenge_id,
        user_id=current_user.id
    )
    db.add(participant)
    db.commit()
    
    return {"message": f"Joined challenge: {challenge.name}"}

# Leaderboards
@router.get("/leaderboard/weekly", response_model=WeeklyLeaderboard)
def get_weekly_leaderboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Calculate current week
    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    
    # Get friend IDs
    friend_ids = []
    friendships = db.query(Friendship).filter(
        or_(
            Friendship.requester_id == current_user.id,
            Friendship.addressee_id == current_user.id
        ),
        Friendship.status == "accepted"
    ).all()
    
    for friendship in friendships:
        friend_id = friendship.addressee_id if friendship.requester_id == current_user.id else friendship.requester_id
        friend_ids.append(friend_id)
    
    # Include current user
    friend_ids.append(current_user.id)
    
    # Get weekly stats for friends
    weekly_stats = db.query(
        CompletedRun.user_id,
        func.sum(CompletedRun.distance_km).label('total_distance'),
        func.count(CompletedRun.id).label('total_runs'),
        func.avg(CompletedRun.avg_pace_s_per_km).label('avg_pace')
    ).filter(
        CompletedRun.user_id.in_(friend_ids),
        CompletedRun.start_datetime >= week_start,
        CompletedRun.start_datetime < week_end
    ).group_by(CompletedRun.user_id).all()
    
    # Create leaderboard entries
    entries = []
    for stats in weekly_stats:
        user = db.query(User).filter(User.id == stats.user_id).first()
        entries.append(LeaderboardEntry(
            user_id=stats.user_id,
            user_name=user.name,
            total_distance=float(stats.total_distance or 0),
            total_runs=stats.total_runs,
            avg_pace=float(stats.avg_pace or 0),
            rank=0  # Will be set after sorting
        ))
    
    # Sort by total distance and assign ranks
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
    # Count friends
    friends_count = db.query(Friendship).filter(
        or_(
            Friendship.requester_id == current_user.id,
            Friendship.addressee_id == current_user.id
        ),
        Friendship.status == "accepted"
    ).count()
    
    # Count activities
    activities_count = db.query(ActivityFeed).filter(
        ActivityFeed.user_id == current_user.id
    ).count()
    
    # Count kudos received
    kudos_received = db.query(Kudos).filter(
        Kudos.receiver_id == current_user.id
    ).count()
    
    # Count kudos given
    kudos_given = db.query(Kudos).filter(
        Kudos.giver_id == current_user.id
    ).count()
    
    # Count completed challenges
    challenges_completed = db.query(ChallengeParticipant).filter(
        ChallengeParticipant.user_id == current_user.id,
        ChallengeParticipant.completed == True
    ).count()
    
    # Count current challenges
    now = datetime.utcnow()
    current_challenges = db.query(ChallengeParticipant).join(
        Challenge, ChallengeParticipant.challenge_id == Challenge.id
    ).filter(
        ChallengeParticipant.user_id == current_user.id,
        Challenge.start_date <= now,
        Challenge.end_date >= now,
        ChallengeParticipant.completed == False
    ).count()
    
    return SocialStats(
        friends_count=friends_count,
        activities_count=activities_count,
        kudos_received=kudos_received,
        kudos_given=kudos_given,
        challenges_completed=challenges_completed,
        current_challenges=current_challenges
    )