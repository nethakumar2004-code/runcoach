from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User
from app.models.achievement import Achievement, UserAchievement
from app.schemas.achievement import UserProfile, BadgeProgress, UserAchievementResponse
from app.dependencies import get_current_user
from app.services.achievements import badge_progress_for, check_and_award_achievements, update_user_stats

router = APIRouter()

@router.get("/profile", response_model=UserProfile)
def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Achievements are awarded when runs are saved; this also catches up older accounts
    check_and_award_achievements(current_user.id, db)
    stats = update_user_stats(current_user.id, db)
    db.commit()

    recent_achievements = (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == current_user.id)
        .order_by(UserAchievement.earned_at.desc())
        .limit(10)
        .all()
    )

    # Use ALL earned achievements here - not just the 10 most recent - or older badges show as unearned
    earned_ids = {
        a_id for (a_id,) in db.query(UserAchievement.achievement_id).filter(UserAchievement.user_id == current_user.id)
    }

    badge_progress = []
    for achievement in db.query(Achievement).all():
        is_earned = achievement.id in earned_ids
        if is_earned:
            progress, progress_text = 1.0, "Completed!"
        else:
            progress, progress_text = badge_progress_for(achievement, stats)
        badge_progress.append(BadgeProgress(
            achievement=achievement,
            progress=progress,
            is_earned=is_earned,
            progress_text=progress_text
        ))

    return UserProfile(
        user_id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        experience_level=current_user.experience_level,
        stats=stats,
        recent_achievements=recent_achievements,
        badge_progress=badge_progress
    )

@router.get("/achievements", response_model=List[UserAchievementResponse])
def get_user_achievements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    achievements = (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == current_user.id)
        .order_by(UserAchievement.earned_at.desc())
        .all()
    )
    return achievements
