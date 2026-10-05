from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.models.user import User
from app.models.training_plan import (
    TrainingPlan, TrainingWorkout, UserTrainingPlan, UserWorkoutCompletion,
    TrainingLevel, WorkoutType,
)
from app.schemas.training_plan import (
    TrainingPlan as TrainingPlanSchema,
    TrainingPlanCreate,
    UserTrainingPlan as UserTrainingPlanSchema,
    WorkoutCompletion as WorkoutCompletionSchema,
    WorkoutCompletionCreate,
    TrainingPlanProgress,
    WeeklyWorkouts
)
from app.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/training-plans", tags=["training-plans"])

# Only mounted when RUNCOACH_DEV_MODE is on (see main.py)
dev_router = APIRouter(prefix="/training-plans", tags=["training-plans (dev only)"])


def _get_active_plan(db: Session, user_id: str) -> UserTrainingPlan:
    user_plan = db.query(UserTrainingPlan).filter(
        UserTrainingPlan.user_id == user_id,
        UserTrainingPlan.is_active == True
    ).order_by(UserTrainingPlan.id.desc()).first()
    if not user_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active training plan found"
        )
    return user_plan


@router.get("/", response_model=List[TrainingPlanSchema])
def get_available_training_plans(
    skip: int = 0,
    limit: int = 100,
    level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all available training plans"""
    query = db.query(TrainingPlan)

    if level:
        try:
            query = query.filter(TrainingPlan.level == TrainingLevel(level.lower()))
        except ValueError:
            raise HTTPException(status_code=400, detail="level must be beginner, intermediate or advanced")

    return query.offset(skip).limit(min(limit, 100)).all()

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
    current_user: User = Depends(require_admin)
):
    """Create a new training plan (admins only, see ADMIN_EMAILS)"""
    # The schema enums and the database enums are different classes, so convert by value
    db_plan = TrainingPlan(
        name=plan.name,
        goal=plan.goal,
        duration_weeks=plan.duration_weeks,
        level=TrainingLevel(plan.level.value),
        description=plan.description
    )
    db.add(db_plan)
    db.flush()  # Get the ID

    for workout_data in plan.workouts:
        fields = workout_data.model_dump()
        fields["workout_type"] = WorkoutType(workout_data.workout_type.value)
        db.add(TrainingWorkout(training_plan_id=db_plan.id, **fields))

    db.commit()
    db.refresh(db_plan)
    return db_plan

@router.post("/enroll/{plan_id}")
def enroll_in_training_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enroll user in a training plan"""
    plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training plan not found"
        )

    # Deactivate every active plan, not just the first one found
    db.query(UserTrainingPlan).filter(
        UserTrainingPlan.user_id == current_user.id,
        UserTrainingPlan.is_active == True
    ).update({UserTrainingPlan.is_active: False})

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
    return _get_active_plan(db, current_user.id)

@router.get("/my/progress", response_model=TrainingPlanProgress)
def get_training_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's training plan progress"""
    user_plan = _get_active_plan(db, current_user.id)

    total_workouts = db.query(TrainingWorkout).filter(
        TrainingWorkout.training_plan_id == user_plan.training_plan_id
    ).count()
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

@router.get("/my/week/{week_number}", response_model=WeeklyWorkouts)
def get_weekly_workouts(
    week_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workouts for a specific week"""
    user_plan = _get_active_plan(db, current_user.id)

    workouts = db.query(TrainingWorkout).filter(
        TrainingWorkout.training_plan_id == user_plan.training_plan_id,
        TrainingWorkout.week_number == week_number
    ).order_by(TrainingWorkout.day_number).all()

    completed_ids = {
        workout_id for (workout_id,) in db.query(UserWorkoutCompletion.workout_id).filter(
            UserWorkoutCompletion.user_plan_id == user_plan.id
        )
    }

    return WeeklyWorkouts(
        week_number=week_number,
        workouts=workouts,
        completed_count=sum(1 for w in workouts if w.id in completed_ids)
    )

@router.post("/workouts/{workout_id}/complete", response_model=WorkoutCompletionSchema)
def complete_workout(
    workout_id: int,
    completion: WorkoutCompletionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a workout as completed"""
    user_plan = _get_active_plan(db, current_user.id)

    workout = db.query(TrainingWorkout).filter(
        TrainingWorkout.id == workout_id,
        TrainingWorkout.training_plan_id == user_plan.training_plan_id
    ).first()
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found"
        )

    existing_completion = db.query(UserWorkoutCompletion).filter(
        UserWorkoutCompletion.user_plan_id == user_plan.id,
        UserWorkoutCompletion.workout_id == workout_id
    ).first()
    if existing_completion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workout already completed"
        )

    workout_completion = UserWorkoutCompletion(
        user_plan_id=user_plan.id,
        workout_id=workout_id,
        **completion.model_dump()
    )
    db.add(workout_completion)
    db.commit()
    db.refresh(workout_completion)
    return workout_completion

@router.put("/my/week", response_model=UserTrainingPlanSchema)
def update_current_week(
    week_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user's current week in training plan"""
    user_plan = _get_active_plan(db, current_user.id)

    if week_number < 1 or week_number > user_plan.training_plan.duration_weeks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid week number"
        )

    user_plan.current_week = week_number
    db.commit()
    db.refresh(user_plan)
    return user_plan


# ---- Development-only endpoints (RUNCOACH_DEV_MODE=1) ----

@dev_router.post("/test-enroll/{plan_id}")
def test_enroll_in_training_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Same as /enroll, kept for the mobile debug screen"""
    return enroll_in_training_plan(plan_id, db, current_user)

@dev_router.get("/debug/user-status")
def debug_user_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to check user's training plan status"""
    try:
        user_plan = _get_active_plan(db, current_user.id)
    except HTTPException:
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

@dev_router.get("/test/week/{plan_id}/{week_number}")
def test_weekly_workouts(
    plan_id: int,
    week_number: int,
    db: Session = Depends(get_db)
):
    """Workouts for a specific week without authentication"""
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
