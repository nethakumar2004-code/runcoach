from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db import Base

class WorkoutType(enum.Enum):
    EASY = "easy"
    TEMPO = "tempo"
    INTERVAL = "interval"
    LONG = "long"
    REST = "rest"

class TrainingLevel(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class TrainingPlan(Base):
    __tablename__ = "training_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    goal = Column(String(200), nullable=False)
    duration_weeks = Column(Integer, nullable=False)
    level = Column(Enum(TrainingLevel), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Note: Relationships commented out to avoid circular import issues
    # workouts = relationship("TrainingWorkout", back_populates="training_plan", cascade="all, delete-orphan")
    # user_plans = relationship("UserTrainingPlan", back_populates="training_plan")

class TrainingWorkout(Base):
    __tablename__ = "training_workouts"

    id = Column(Integer, primary_key=True, index=True)
    training_plan_id = Column(Integer, ForeignKey("training_plans.id"), nullable=False)
    week_number = Column(Integer, nullable=False)
    day_number = Column(Integer, nullable=False)
    workout_type = Column(Enum(WorkoutType), nullable=False)
    duration_minutes = Column(Integer)
    distance_km = Column(Float)
    description = Column(Text, nullable=False)
    intensity_level = Column(Integer, default=1)  # 1-10 scale
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Note: Relationships commented out to avoid circular import issues
    # training_plan = relationship("TrainingPlan", back_populates="workouts")
    # user_workouts = relationship("UserWorkoutCompletion", back_populates="workout")

class UserTrainingPlan(Base):
    __tablename__ = "user_training_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    training_plan_id = Column(Integer, ForeignKey("training_plans.id"), nullable=False)
    current_week = Column(Integer, default=1)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Note: Relationships commented out to avoid circular import issues
    # user = relationship("User", back_populates="training_plans")
    # training_plan = relationship("TrainingPlan", back_populates="user_plans")
    # workout_completions = relationship("UserWorkoutCompletion", back_populates="user_plan")

class UserWorkoutCompletion(Base):
    __tablename__ = "user_workout_completions"

    id = Column(Integer, primary_key=True, index=True)
    user_plan_id = Column(Integer, ForeignKey("user_training_plans.id"), nullable=False)
    workout_id = Column(Integer, ForeignKey("training_workouts.id"), nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    actual_duration_minutes = Column(Integer)
    actual_distance_km = Column(Float)
    effort_rating = Column(Integer)  # 1-10 scale
    notes = Column(Text)

    # Note: Relationships commented out to avoid circular import issues
    # user_plan = relationship("UserTrainingPlan", back_populates="workout_completions")
    # workout = relationship("TrainingWorkout", back_populates="user_workouts")