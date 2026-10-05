from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
import uuid
from app.timeutils import utcnow
from app.db import Base

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String, nullable=False)  # emoji or icon name
    category = Column(String, nullable=False)  # distance, speed, consistency, milestone
    requirement_type = Column(String, nullable=False)  # total_distance, single_run, streak, etc.
    requirement_value = Column(Float, nullable=False)
    points = Column(Integer, default=10)
    rarity = Column(String, default="common")  # common, rare, epic, legendary

class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(String, ForeignKey("achievements.id"), nullable=False)
    earned_at = Column(DateTime, default=utcnow)
    progress = Column(Float, default=0.0)  # for tracking progress towards achievement
    
    # Relationships
    achievement = relationship("Achievement")

class UserStats(Base):
    __tablename__ = "user_stats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Running stats
    total_distance_km = Column(Float, default=0.0)
    total_runs = Column(Integer, default=0)
    total_time_minutes = Column(Float, default=0.0)
    best_pace_per_km = Column(Float, nullable=True)
    longest_run_km = Column(Float, default=0.0)
    current_streak_days = Column(Integer, default=0)
    longest_streak_days = Column(Integer, default=0)
    
    # Achievement stats
    total_points = Column(Integer, default=0)
    level = Column(Integer, default=1)
    
    # Weekly/Monthly stats
    this_week_distance = Column(Float, default=0.0)
    this_month_distance = Column(Float, default=0.0)
    
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)