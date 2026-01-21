from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class AchievementBase(BaseModel):
    name: str
    description: str
    icon: str
    category: str
    requirement_type: str
    requirement_value: float
    points: int = 10
    rarity: str = "common"

class Achievement(AchievementBase):
    id: str
    
    class Config:
        from_attributes = True

class UserAchievementResponse(BaseModel):
    id: str
    achievement: Achievement
    earned_at: datetime
    progress: float
    
    class Config:
        from_attributes = True

class UserStatsResponse(BaseModel):
    total_distance_km: float
    total_runs: int
    total_time_minutes: float
    best_pace_per_km: Optional[float]
    longest_run_km: float
    current_streak_days: int
    longest_streak_days: int
    total_points: int
    level: int
    this_week_distance: float
    this_month_distance: float
    
    class Config:
        from_attributes = True

class BadgeProgress(BaseModel):
    achievement: Achievement
    progress: float
    is_earned: bool
    progress_text: str

class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str
    experience_level: Optional[str]
    stats: UserStatsResponse
    recent_achievements: List[UserAchievementResponse]
    badge_progress: List[BadgeProgress]