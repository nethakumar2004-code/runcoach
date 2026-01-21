from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Friend Schemas
class FriendRequest(BaseModel):
    email: str

class FriendshipResponse(BaseModel):
    id: str
    requester_id: str
    addressee_id: str
    status: str
    created_at: datetime
    friend_name: str
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
    user_name: str
    activity_type: str
    activity_data: Optional[str] = None
    created_at: datetime
    likes_count: int
    comments_count: int
    user_liked: bool

class ActivityComment(BaseModel):
    comment_text: str

class ActivityCommentResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    comment_text: str
    created_at: datetime

# Challenge Schemas
class ChallengeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    challenge_type: str  # distance, time, frequency
    target_value: int
    start_date: datetime
    end_date: datetime
    is_public: bool = True

class ChallengeResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    challenge_type: str
    target_value: int
    start_date: datetime
    end_date: datetime
    created_by: str
    creator_name: str
    is_public: bool
    participants_count: int
    user_participating: bool
    user_progress: int
    user_completed: bool

class ChallengeParticipantResponse(BaseModel):
    user_id: str
    user_name: str
    current_progress: int
    completed: bool
    joined_at: datetime

class ChallengeLeaderboard(BaseModel):
    challenge: ChallengeResponse
    participants: List[ChallengeParticipantResponse]

# Kudos Schemas
class KudosResponse(BaseModel):
    id: str
    giver_id: str
    giver_name: str
    created_at: datetime

# Leaderboard Schemas
class LeaderboardEntry(BaseModel):
    user_id: str
    user_name: str
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