from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Literal, Optional
from datetime import datetime

from app.timeutils import to_naive_utc

# Friend Schemas
class FriendRequest(BaseModel):
    email: str

class FriendshipResponse(BaseModel):
    id: str
    requester_id: str
    addressee_id: str
    status: str
    created_at: datetime
    friend_name: Optional[str] = None
    friend_email: str

class FriendsList(BaseModel):
    friends: List[FriendshipResponse]
    pending_requests: List[FriendshipResponse]
    sent_requests: List[FriendshipResponse]

# Activity Feed Schemas
class ActivityCreate(BaseModel):
    activity_type: str
    activity_data: Optional[str] = None
    is_public: bool = True

class ActivityResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    activity_type: str
    activity_data: Optional[str] = None
    created_at: datetime
    likes_count: int
    comments_count: int
    user_liked: bool

class ActivityComment(BaseModel):
    comment_text: str = Field(min_length=1, max_length=1000)

class ActivityCommentResponse(BaseModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    comment_text: str
    created_at: datetime

# Challenge Schemas
class ChallengeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=2000)
    challenge_type: Literal["distance", "time", "frequency"]  # km, minutes, number of runs
    target_value: int = Field(gt=0)
    start_date: datetime
    end_date: datetime
    is_public: bool = True

    @field_validator("start_date", "end_date")
    @classmethod
    def normalise_dates(cls, value: datetime) -> datetime:
        return to_naive_utc(value)

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

class ChallengeResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    challenge_type: str
    target_value: int
    start_date: datetime
    end_date: datetime
    created_by: str
    creator_name: Optional[str] = None
    is_public: bool
    participants_count: int
    user_participating: bool
    user_progress: int
    user_completed: bool

class ChallengeParticipantResponse(BaseModel):
    user_id: str
    user_name: Optional[str] = None
    current_progress: int
    completed: bool
    joined_at: datetime

class ChallengeLeaderboard(BaseModel):
    challenge: ChallengeResponse
    participants: List[ChallengeParticipantResponse]

# Kudos Schemas
class KudosToggleResponse(BaseModel):
    run_id: str
    given: bool
    kudos_count: int

class KudosResponse(BaseModel):
    id: str
    giver_id: str
    giver_name: Optional[str] = None
    created_at: datetime

# Leaderboard Schemas
class LeaderboardEntry(BaseModel):
    user_id: str
    user_name: Optional[str] = None
    total_distance: float
    total_runs: int
    avg_pace: float
    rank: int

class WeeklyLeaderboard(BaseModel):
    week_start: datetime
    week_end: datetime
    entries: List[LeaderboardEntry]

# Social Stats
class SocialStats(BaseModel):
    friends_count: int
    activities_count: int
    kudos_received: int
    kudos_given: int
    challenges_completed: int
    current_challenges: int