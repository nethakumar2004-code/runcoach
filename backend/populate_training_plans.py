#!/usr/bin/env python3
"""
Script to populate the database with sample training plans
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db import SessionLocal, engine, Base

# Import all models to ensure proper relationships
from app.models.user import User
from app.models.weather import WeatherAlert, WeatherData
from app.models.training_plan import TrainingPlan, TrainingWorkout, WorkoutType, TrainingLevel
from app.models.run import CompletedRun
from app.models.goal import Goal
from app.models.workout import PlannedWorkout
from app.models.achievement import Achievement, UserAchievement, UserStats
from app.models.social import Friendship, ActivityFeed, ActivityLike, ActivityComment, Challenge, ChallengeParticipant, Kudos

# Create all tables
Base.metadata.create_all(bind=engine)

def create_sample_plans():
    db = SessionLocal()
    
    try:
        # 5K Beginner Plan
        plan_5k = TrainingPlan(
            name="5K Training Plan",
            goal="Complete your first 5K",
            duration_weeks=8,
            level=TrainingLevel.BEGINNER,
            description="A beginner-friendly 8-week plan to get you ready for your first 5K race"
        )
        db.add(plan_5k)
        db.flush()
        
        # Week 1 workouts for 5K plan
        workouts_5k_w1 = [
            TrainingWorkout(training_plan_id=plan_5k.id, week_number=1, day_number=1, workout_type=WorkoutType.EASY, duration_minutes=20, distance_km=2, description="Easy run - maintain conversational pace", intensity_level=3),
            TrainingWorkout(training_plan_id=plan_5k.id, week_number=1, day_number=2, workout_type=WorkoutType.REST, duration_minutes=0, description="Rest day or light cross-training", intensity_level=1),
            TrainingWorkout(training_plan_id=plan_5k.id, week_number=1, day_number=3, workout_type=WorkoutType.INTERVAL, duration_minutes=25, description="5x 1min fast, 2min recovery", intensity_level=7),
            TrainingWorkout(training_plan_id=plan_5k.id, week_number=1, day_number=4, workout_type=WorkoutType.REST, duration_minutes=0, description="Rest day", intensity_level=1),
            TrainingWorkout(training_plan_id=plan_5k.id, week_number=1, day_number=5, workout_type=WorkoutType.TEMPO, duration_minutes=30, distance_km=3, description="Comfortably hard pace for 15 minutes", intensity_level=6),
            TrainingWorkout(training_plan_id=plan_5k.id, week_number=1, day_number=6, workout_type=WorkoutType.REST, duration_minutes=0, description="Rest day", intensity_level=1),
            TrainingWorkout(training_plan_id=plan_5k.id, week_number=1, day_number=7, workout_type=WorkoutType.LONG, duration_minutes=35, distance_km=4, description="Long easy run", intensity_level=4),
        ]
        
        for workout in workouts_5k_w1:
            db.add(workout)
        
        # 10K Intermediate Plan
        plan_10k = TrainingPlan(
            name="10K Training Plan",
            goal="Build endurance for 10K",
            duration_weeks=12,
            level=TrainingLevel.INTERMEDIATE,
            description="A 12-week intermediate plan to improve your 10K performance"
        )
        db.add(plan_10k)
        db.flush()
        
        # Week 1 workouts for 10K plan
        workouts_10k_w1 = [
            TrainingWorkout(training_plan_id=plan_10k.id, week_number=1, day_number=1, workout_type=WorkoutType.EASY, duration_minutes=30, distance_km=4, description="Easy aerobic run", intensity_level=3),
            TrainingWorkout(training_plan_id=plan_10k.id, week_number=1, day_number=2, workout_type=WorkoutType.REST, duration_minutes=0, description="Rest day or cross-training", intensity_level=1),
            TrainingWorkout(training_plan_id=plan_10k.id, week_number=1, day_number=3, workout_type=WorkoutType.INTERVAL, duration_minutes=40, description="6x 3min at 10K pace, 90sec recovery", intensity_level=8),
            TrainingWorkout(training_plan_id=plan_10k.id, week_number=1, day_number=4, workout_type=WorkoutType.EASY, duration_minutes=25, distance_km=3, description="Recovery run", intensity_level=2),
            TrainingWorkout(training_plan_id=plan_10k.id, week_number=1, day_number=5, workout_type=WorkoutType.TEMPO, duration_minutes=45, distance_km=6, description="Threshold run - comfortably hard", intensity_level=7),
            TrainingWorkout(training_plan_id=plan_10k.id, week_number=1, day_number=6, workout_type=WorkoutType.REST, duration_minutes=0, description="Rest day", intensity_level=1),
            TrainingWorkout(training_plan_id=plan_10k.id, week_number=1, day_number=7, workout_type=WorkoutType.LONG, duration_minutes=60, distance_km=8, description="Long steady run", intensity_level=4),
        ]
        
        for workout in workouts_10k_w1:
            db.add(workout)
        
        # Half Marathon Advanced Plan
        plan_half = TrainingPlan(
            name="Half Marathon Plan",
            goal="Complete 21.1K distance",
            duration_weeks=16,
            level=TrainingLevel.ADVANCED,
            description="A comprehensive 16-week plan for experienced runners targeting half marathon"
        )
        db.add(plan_half)
        db.flush()
        
        # Week 1 workouts for Half Marathon plan
        workouts_half_w1 = [
            TrainingWorkout(training_plan_id=plan_half.id, week_number=1, day_number=1, workout_type=WorkoutType.EASY, duration_minutes=45, distance_km=6, description="Recovery run", intensity_level=3),
            TrainingWorkout(training_plan_id=plan_half.id, week_number=1, day_number=2, workout_type=WorkoutType.INTERVAL, duration_minutes=50, description="5x 1K at 5K pace, 400m recovery", intensity_level=9),
            TrainingWorkout(training_plan_id=plan_half.id, week_number=1, day_number=3, workout_type=WorkoutType.EASY, duration_minutes=35, distance_km=5, description="Easy run", intensity_level=3),
            TrainingWorkout(training_plan_id=plan_half.id, week_number=1, day_number=4, workout_type=WorkoutType.TEMPO, duration_minutes=60, distance_km=10, description="Half marathon pace run", intensity_level=7),
            TrainingWorkout(training_plan_id=plan_half.id, week_number=1, day_number=5, workout_type=WorkoutType.EASY, duration_minutes=30, distance_km=4, description="Recovery run", intensity_level=2),
            TrainingWorkout(training_plan_id=plan_half.id, week_number=1, day_number=6, workout_type=WorkoutType.REST, duration_minutes=0, description="Rest day", intensity_level=1),
            TrainingWorkout(training_plan_id=plan_half.id, week_number=1, day_number=7, workout_type=WorkoutType.LONG, duration_minutes=90, distance_km=15, description="Long run with negative splits", intensity_level=5),
        ]
        
        for workout in workouts_half_w1:
            db.add(workout)
        
        db.commit()
        print("Sample training plans created successfully!")
        
    except Exception as e:
        print(f"Error creating sample plans: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_plans()