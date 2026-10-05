"""Social helpers: friend lookups, the activity feed and challenge progress."""
import json
import math
from typing import List

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.run import CompletedRun
from app.models.social import ActivityFeed, Challenge, ChallengeParticipant, Friendship


def get_friend_ids(db: Session, user_id: str) -> List[str]:
    friendships = db.query(Friendship).filter(
        or_(Friendship.requester_id == user_id, Friendship.addressee_id == user_id),
        Friendship.status == "accepted",
    ).all()
    return [f.addressee_id if f.requester_id == user_id else f.requester_id for f in friendships]


def are_friends(db: Session, user_a: str, user_b: str) -> bool:
    return user_b in get_friend_ids(db, user_a)


def record_activity(db: Session, user_id: str, activity_type: str, data: dict, is_public: bool = True) -> ActivityFeed:
    """Add an item to the activity feed (the caller commits)."""
    activity = ActivityFeed(
        user_id=user_id,
        activity_type=activity_type,
        activity_data=json.dumps(data),
        is_public=is_public,
    )
    db.add(activity)
    return activity


def challenge_progress(db: Session, challenge: Challenge, user_id: str) -> int:
    """Progress from the user's runs inside the challenge window.

    distance -> whole km, time -> whole minutes, frequency -> number of runs.
    Recomputed from scratch each time, so it can never drift or double count.
    """
    runs = db.query(CompletedRun).filter(
        CompletedRun.user_id == user_id,
        CompletedRun.start_datetime >= challenge.start_date,
        CompletedRun.start_datetime <= challenge.end_date,
    ).all()
    if challenge.challenge_type == "distance":
        return math.floor(sum(r.distance_km for r in runs))
    if challenge.challenge_type == "time":
        return math.floor(sum(r.duration_sec for r in runs) / 60)
    if challenge.challenge_type == "frequency":
        return len(runs)
    return 0


def refresh_participation(db: Session, participation: ChallengeParticipant, challenge: Challenge):
    participation.current_progress = challenge_progress(db, challenge, participation.user_id)
    participation.completed = participation.current_progress >= challenge.target_value


def update_challenge_progress(db: Session, user_id: str):
    """Refresh progress on every challenge the user takes part in (the caller commits)."""
    rows = db.query(ChallengeParticipant, Challenge).join(
        Challenge, ChallengeParticipant.challenge_id == Challenge.id
    ).filter(ChallengeParticipant.user_id == user_id).all()
    for participation, challenge in rows:
        refresh_participation(db, participation, challenge)
