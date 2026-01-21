from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class WorkoutType(str, Enum):
    EASY = "easy"
    TEMPO = "tempo"
    INTERVAL = "interval"
    LONG = "long"
    REST = "rest"

class TrainingLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class TrainingWorkoutBase(BaseModel):
    week_number: int
    day_number: int
    workout_type: WorkoutType
    duration_minutes: Optional[int] = None
    distance_km: Optional[float] = None
    description: str
    intensity_level: Optional[int] = 1

class TrainingWorkoutCreate(TrainingWorkoutBase):
    pass

class TrainingWorkout(TrainingWorkoutBase):
    id: int
    training_plan_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TrainingPlanBase(BaseModel):
    name: str
    goal: str
    duration_weeks: int
    level: TrainingLevel
    description: Optional[str] = None

class TrainingPlanCreate(TrainingPlanBase):
    workouts: List[TrainingWorkoutCreate]

class TrainingPlan(TrainingPlanBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    workouts: List[TrainingWorkout] = []

    class Config:
        from_attributes = True

class UserTrainingPlanBase(BaseModel):
    training_plan_id: int
    current_week: Optional[int] = 1

class UserTrainingPlanCreate(UserTrainingPlanBase):
    pass

class UserTrainingPlan(UserTrainingPlanBase):
    id: int
    user_id: str
    start_date: datetime
    is_active: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    training_plan: TrainingPlan

    class Config:
        from_attributes = True

class WorkoutCompletionBase(BaseModel):
    actual_duration_minutes: Optional[int] = None
    actual_distance_km: Optional[float] = None
    effort_rating: Optional[int] = None
    notes: Optional[str] = None

class WorkoutCompletionCreate(WorkoutCompletionBase):
    pass

class WorkoutCompletion(WorkoutCompletionBase):
    id: int
    user_plan_id: int
    workout_id: int
    completed_at: datetime
    workout: TrainingWorkout

    class Config:
        from_attributes = True

class TrainingPlanProgress(BaseModel):
    total_workouts: int
    completed_workouts: int
    completion_percentage: float
    current_week: int
    total_weeks: int
    weeks_remaining: int

class WeeklyWorkouts(BaseModel):
    week_number: int
    workouts: List[TrainingWorkout]
    completed_count: int