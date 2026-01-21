from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from app.db import get_db
from app.models.user import User
from app.models.training_plan import TrainingPlan, TrainingWorkout, UserTrainingPlan, UserWorkoutCompletion
from app.schemas.training_plan import (
    TrainingPlan as TrainingPlanSchema,
    TrainingPlanCreate,
    UserTrainingPlan as UserTrainingPlanSchema,
    UserTrainingPlanCreate,
    WorkoutCompletion as WorkoutCompletionSchema,
    WorkoutCompletionCreate,
    TrainingPlanProgress,
    WeeklyWorkouts
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/training-plans", tags=["training-plans"])

@router.get("/", response_model=List[TrainingPlanSchema])
def get_available_training_plans(
    skip: int = 0,
    limit: int = 100,
    level: str = None,
    db: Session = Depends(get_db)
):
    """Get all available training plans"""
    query = db.query(TrainingPlan)
    
    if level:
        query = query.filter(TrainingPlan.level == level)
    
    plans = query.offset(skip).limit(limit).all()
    return plans

@router.get("/{plan_id}", response_model=TrainingPlanSchema)
def get_training_plan(
    plan_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific training plan with workouts"""
    plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training plan not found"
        )
    return plan

@router.post("/", response_model=TrainingPlanSchema)
def create_training_plan(
    plan: TrainingPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new training plan (admin only)"""
    # In a real app, you'd check if user is admin
    db_plan = TrainingPlan(
        name=plan.name,
        goal=plan.goal,
        duration_weeks=plan.duration_weeks,
        level=plan.level,
        description=plan.description
    )
    db.add(db_plan)
    db.flush()  # Get the ID
    
    # Add workouts
    for workout_data in plan.workouts:
        workout = TrainingWorkout(
            training_plan_id=db_plan.id,
            **workout_data.dict()
        )
        db.add(workout)
    
    db.commit()
    db.refresh(db_plan)
    return db_plan

@router.post("/test-enroll/{plan_id}")
def test_enroll_in_training_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test enrollment endpoint with detailed logging"""
    try:
        print(f"Test enrollment - User ID: {current_user.id}, Plan ID: {plan_id}")
        
        # Check if plan exists
        plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
        if not plan:
            print(f"Plan {plan_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training plan not found"
            )
        
        print(f"Found plan: {plan.name}")
        
        # Check if user already has an active plan
        existing_plan = db.query(UserTrainingPlan).filter(
            UserTrainingPlan.user_id == current_user.id,
            UserTrainingPlan.is_active == True
        ).first()
        
        if existing_plan:
            print(f"User has existing active plan: {existing_plan.id}")
            # Deactivate existing plan
            existing_plan.is_active = False
        else:
            print("No existing active plan found")
        
        # Create new enrollment
        user_plan = UserTrainingPlan(
            user_id=current_user.id,
            training_plan_id=plan_id,
            current_week=1,
            is_active=True
        )
        
        db.add(user_plan)
        db.commit()
        db.refresh(user_plan)
        
        print(f"Successfully enrolled user in plan. User plan ID: {user_plan.id}")
        
        return {
            "success": True,
            "user_plan_id": user_plan.id,
            "plan_name": plan.name,
            "current_week": user_plan.current_week,
            "message": "Successfully enrolled in training plan"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in test enrollment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/enroll/{plan_id}")
def enroll_in_training_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enroll user in a training plan"""
    # Check if plan exists
    plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training plan not found"
        )
    
    # Check if user already has an active plan
    existing_plan = db.query(UserTrainingPlan).filter(
        UserTrainingPlan.user_id == current_user.id,
        UserTrainingPlan.is_active == True
    ).first()
    
    if existing_plan:
        # Deactivate existing plan
        existing_plan.is_active = False
    
    # Create new enrollment
    user_plan = UserTrainingPlan(
        user_id=current_user.id,
        training_plan_id=plan_id,
        current_week=1,
        is_active=True
    )
    
    db.add(user_plan)
    db.commit()
    db.refresh(user_plan)
    
    return {
        "success": True,
        "user_plan_id": user_plan.id,
        "plan_name": plan.name,
        "current_week": user_plan.current_week,
        "message": "Successfully enrolled in training plan"
    }

@router.get("/my/current", response_model=UserTrainingPlanSchema)
def get_current_training_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's current active training plan"""
    user_plan = db.query(UserTrainingPlan).filter(
        UserTrainingPlan.user_id == current_user.id,
        UserTrainingPlan.is_active == True
    ).first()
    
    if not user_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active training plan found"
        )
    
    return user_plan

@router.get("/my/progress", response_model=TrainingPlanProgress)
def get_training_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's training plan progress"""
    user_plan = db.query(UserTrainingPlan).filter(
        UserTrainingPlan.user_id == current_user.id,
        UserTrainingPlan.is_active == True
    ).first()
    
    if not user_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active training plan found"
        )
    
    # Get total workouts
    total_workouts = db.query(TrainingWorkout).filter(
        TrainingWorkout.training_plan_id == user_plan.training_plan_id
    ).count()
    
    # Get completed workouts
    completed_workouts = db.query(UserWorkoutCompletion).filter(
        UserWorkoutCompletion.user_plan_id == user_plan.id
    ).count()
    
    completion_percentage = (completed_workouts / total_workouts * 100) if total_workouts > 0 else 0
    weeks_remaining = user_plan.training_plan.duration_weeks - user_plan.current_week + 1
    
    return TrainingPlanProgress(
        total_workouts=total_workouts,
        completed_workouts=completed_workouts,
        completion_percentage=completion_percentage,
        current_week=user_plan.current_week,
        total_weeks=user_plan.training_plan.duration_weeks,
        weeks_remaining=max(0, weeks_remaining)
    )

@router.get("/debug/user-status")
def debug_user_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to check user's training plan status"""
    user_plan = db.query(UserTrainingPlan).filter(
        UserTrainingPlan.user_id == current_user.id,
        UserTrainingPlan.is_active == True
    ).first()
    
    if not user_plan:
        return {
            "user_id": current_user.id,
            "has_active_plan": False,
            "message": "No active training plan found"
        }
    
    workouts = db.query(TrainingWorkout).filter(
        TrainingWorkout.training_plan_id == user_plan.training_plan_id,
        TrainingWorkout.week_number == user_plan.current_week
    ).all()
    
    completed_workouts = db.query(UserWorkoutCompletion).filter(
        UserWorkoutCompletion.user_plan_id == user_plan.id
    ).all()
    
    return {
        "user_id": current_user.id,
        "has_active_plan": True,
        "plan_id": user_plan.training_plan_id,
        "plan_name": user_plan.training_plan.name,
        "current_week": user_plan.current_week,
        "workouts_this_week": len(workouts),
        "total_completed": len(completed_workouts),
        "workout_ids_this_week": [w.id for w in workouts],
        "completed_workout_ids": [c.workout_id for c in completed_workouts]
    }

@router.get("/test/week/{plan_id}/{week_number}")
def test_weekly_workouts(
    plan_id: int,
    week_number: int,
    db: Session = Depends(get_db)
):
    """Test endpoint to get workouts for a specific week without authentication"""
    # Get workouts for the week
    workouts = db.query(TrainingWorkout).filter(
        TrainingWorkout.training_plan_id == plan_id,
        TrainingWorkout.week_number == week_number
    ).order_by(TrainingWorkout.day_number).all()
    
    return {
        "plan_id": plan_id,
        "week_number": week_number,
        "workouts": [
            {
                "id": w.id,
                "day_number": w.day_number,
                "workout_type": w.workout_type.value,
                "description": w.description,
                "duration_minutes": w.duration_minutes,
                "distance_km": w.distance_km,
                "intensity_level": w.intensity_level
            } for w in workouts
        ],
        "workout_count": len(workouts)
    }

@router.get("/my/week/{week_number}", response_model=WeeklyWorkouts)
def get_weekly_workouts(
    week_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workouts for a specific week"""
    try:
        user_plan = db.query(UserTrainingPlan).filter(
            UserTrainingPlan.user_id == current_user.id,
            UserTrainingPlan.is_active == True
        ).first()
        
        if not user_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active training plan found"
            )
        
        # Get workouts for the week
        workouts = db.query(TrainingWorkout).filter(
            TrainingWorkout.training_plan_id == user_plan.training_plan_id,
            TrainingWorkout.week_number == week_number
        ).order_by(TrainingWorkout.day_number).all()
        
        # Get completed workout IDs - handle case where no completions exist
        completed_workout_ids = db.query(UserWorkoutCompletion.workout_id).filter(
            UserWorkoutCompletion.user_plan_id == user_plan.id
        ).all()
        
        completed_ids = [c[0] for c in completed_workout_ids] if completed_workout_ids else []
        completed_count = len([w for w in workouts if w.id in completed_ids])
        
        return WeeklyWorkouts(
            week_number=week_number,
            workouts=workouts,
            completed_count=completed_count
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Error in get_weekly_workouts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/workouts/{workout_id}/complete", response_model=WorkoutCompletionSchema)
def complete_workout(
    workout_id: int,
    completion: WorkoutCompletionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a workout as completed"""
    try:
        print(f"Attempting to complete workout {workout_id} for user {current_user.id}")
        print(f"Completion data: {completion}")
        
        user_plan = db.query(UserTrainingPlan).filter(
            UserTrainingPlan.user_id == current_user.id,
            UserTrainingPlan.is_active == True
        ).first()
        
        if not user_plan:
            print(f"No active training plan found for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active training plan found"
            )
        
        print(f"Found user plan: {user_plan.id}")
        
        # Check if workout exists and belongs to the plan
        workout = db.query(TrainingWorkout).filter(
            TrainingWorkout.id == workout_id,
            TrainingWorkout.training_plan_id == user_plan.training_plan_id
        ).first()
        
        if not workout:
            print(f"Workout {workout_id} not found or doesn't belong to plan {user_plan.training_plan_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found"
            )
        
        print(f"Found workout: {workout.id} - {workout.description}")
        
        # Check if already completed
        existing_completion = db.query(UserWorkoutCompletion).filter(
            UserWorkoutCompletion.user_plan_id == user_plan.id,
            UserWorkoutCompletion.workout_id == workout_id
        ).first()
        
        if existing_completion:
            print(f"Workout {workout_id} already completed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workout already completed"
            )
        
        # Create completion record
        workout_completion = UserWorkoutCompletion(
            user_plan_id=user_plan.id,
            workout_id=workout_id,
            actual_duration_minutes=completion.actual_duration_minutes,
            actual_distance_km=completion.actual_distance_km,
            effort_rating=completion.effort_rating,
            notes=completion.notes
        )
        
        db.add(workout_completion)
        db.commit()
        db.refresh(workout_completion)
        
        print(f"Successfully completed workout {workout_id}")
        return workout_completion
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error completing workout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.put("/my/week", response_model=UserTrainingPlanSchema)
def update_current_week(
    week_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user's current week in training plan"""
    user_plan = db.query(UserTrainingPlan).filter(
        UserTrainingPlan.user_id == current_user.id,
        UserTrainingPlan.is_active == True
    ).first()
    
    if not user_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active training plan found"
        )
    
    if week_number < 1 or week_number > user_plan.training_plan.duration_weeks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid week number"
        )
    
    user_plan.current_week = week_number
    db.commit()
    db.refresh(user_plan)
    return user_plan