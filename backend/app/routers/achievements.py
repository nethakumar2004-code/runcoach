from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.db import get_db
from app.models.user import User
from app.models.run import CompletedRun
from app.models.achievement import Achievement, UserAchievement, UserStats
from app.schemas.achievement import UserProfile, UserStatsResponse, BadgeProgress, UserAchievementResponse
from app.dependencies import get_current_user

router = APIRouter()

def initialize_default_achievements(db: Session):
    """Initialize default achievements if they don't exist"""
    existing = db.query(Achievement).first()
    if existing:
        return
    
    achievements = [
        # Distance milestones
        {"name": "First Steps", "description": "Complete your first run", "icon": "👟", "category": "milestone", "requirement_type": "total_runs", "requirement_value": 1, "points": 10, "rarity": "common"},
        {"name": "5K Hero", "description": "Run 5 kilometers in a single run", "icon": "🏃", "category": "distance", "requirement_type": "single_run_distance", "requirement_value": 5.0, "points": 25, "rarity": "common"},
        {"name": "10K Warrior", "description": "Run 10 kilometers in a single run", "icon": "🏃‍♂️", "category": "distance", "requirement_type": "single_run_distance", "requirement_value": 10.0, "points": 50, "rarity": "rare"},
        {"name": "Half Marathon Hero", "description": "Run 21.1 kilometers in a single run", "icon": "🏅", "category": "distance", "requirement_type": "single_run_distance", "requirement_value": 21.1, "points": 100, "rarity": "epic"},
        {"name": "Marathon Legend", "description": "Run 42.2 kilometers in a single run", "icon": "👑", "category": "distance", "requirement_type": "single_run_distance", "requirement_value": 42.2, "points": 200, "rarity": "legendary"},
        
        # Total distance achievements
        {"name": "Century Club", "description": "Run 100 total kilometers", "icon": "💯", "category": "distance", "requirement_type": "total_distance", "requirement_value": 100.0, "points": 75, "rarity": "rare"},
        {"name": "Distance Demon", "description": "Run 500 total kilometers", "icon": "😈", "category": "distance", "requirement_type": "total_distance", "requirement_value": 500.0, "points": 150, "rarity": "epic"},
        {"name": "Ultra Runner", "description": "Run 1000 total kilometers", "icon": "🚀", "category": "distance", "requirement_type": "total_distance", "requirement_value": 1000.0, "points": 300, "rarity": "legendary"},
        
        # Consistency achievements
        {"name": "Consistent Runner", "description": "Run 3 days in a row", "icon": "🔥", "category": "consistency", "requirement_type": "streak_days", "requirement_value": 3, "points": 20, "rarity": "common"},
        {"name": "Week Warrior", "description": "Run 7 days in a row", "icon": "⚡", "category": "consistency", "requirement_type": "streak_days", "requirement_value": 7, "points": 40, "rarity": "rare"},
        {"name": "Unstoppable", "description": "Run 30 days in a row", "icon": "🌟", "category": "consistency", "requirement_type": "streak_days", "requirement_value": 30, "points": 100, "rarity": "epic"},
        
        # Speed achievements
        {"name": "Speed Demon", "description": "Run faster than 4:00 min/km", "icon": "💨", "category": "speed", "requirement_type": "best_pace", "requirement_value": 240, "points": 60, "rarity": "rare"},
        {"name": "Lightning Fast", "description": "Run faster than 3:30 min/km", "icon": "⚡", "category": "speed", "requirement_type": "best_pace", "requirement_value": 210, "points": 120, "rarity": "epic"},
        
        # Frequency achievements
        {"name": "Regular Runner", "description": "Complete 10 runs", "icon": "🎯", "category": "milestone", "requirement_type": "total_runs", "requirement_value": 10, "points": 30, "rarity": "common"},
        {"name": "Running Addict", "description": "Complete 50 runs", "icon": "🏆", "category": "milestone", "requirement_type": "total_runs", "requirement_value": 50, "points": 80, "rarity": "rare"},
        {"name": "Running Machine", "description": "Complete 100 runs", "icon": "🤖", "category": "milestone", "requirement_type": "total_runs", "requirement_value": 100, "points": 150, "rarity": "epic"},
    ]
    
    for ach_data in achievements:
        achievement = Achievement(**ach_data)
        db.add(achievement)
    
    db.commit()

def update_user_stats(user_id: str, db: Session):
    """Update user statistics based on their runs"""
    # Get or create user stats
    stats = db.query(UserStats).filter(UserStats.user_id == user_id).first()
    if not stats:
        stats = UserStats(user_id=user_id)
        db.add(stats)
    
    # Ensure total_points is not None
    if stats.total_points is None:
        stats.total_points = 0
    
    # Calculate stats from runs
    runs = db.query(CompletedRun).filter(CompletedRun.user_id == user_id).all()
    
    if runs:
        stats.total_runs = len(runs)
        stats.total_distance_km = sum(run.distance_km for run in runs)
        stats.total_time_minutes = sum(run.duration_sec / 60 for run in runs)
        stats.longest_run_km = max(run.distance_km for run in runs)
        
        # Best pace (fastest pace in seconds per km)
        paces = [run.avg_pace_s_per_km for run in runs if run.avg_pace_s_per_km > 0]
        if paces:
            stats.best_pace_per_km = min(paces)
    
    # Calculate level based on points (ensure total_points is not None)
    stats.level = max(1, (stats.total_points or 0) // 100 + 1)
    
    db.commit()
    return stats

def check_and_award_achievements(user_id: str, db: Session):
    """Check if user has earned any new achievements"""
    stats = update_user_stats(user_id, db)
    achievements = db.query(Achievement).all()
    user_achievements = db.query(UserAchievement).filter(UserAchievement.user_id == user_id).all()
    earned_achievement_ids = {ua.achievement_id for ua in user_achievements}
    
    new_achievements = []
    
    for achievement in achievements:
        if achievement.id in earned_achievement_ids:
            continue
            
        earned = False
        
        if achievement.requirement_type == "total_runs":
            earned = (stats.total_runs or 0) >= achievement.requirement_value
        elif achievement.requirement_type == "total_distance":
            earned = (stats.total_distance_km or 0) >= achievement.requirement_value
        elif achievement.requirement_type == "single_run_distance":
            earned = (stats.longest_run_km or 0) >= achievement.requirement_value
        elif achievement.requirement_type == "best_pace":
            earned = stats.best_pace_per_km and stats.best_pace_per_km <= achievement.requirement_value
        elif achievement.requirement_type == "streak_days":
            earned = (stats.current_streak_days or 0) >= achievement.requirement_value
        
        if earned:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
                progress=1.0
            )
            db.add(user_achievement)
            # Ensure total_points is not None before adding
            if stats.total_points is None:
                stats.total_points = 0
            stats.total_points += achievement.points
            new_achievements.append(achievement)
    
    db.commit()
    return new_achievements

@router.get("/profile", response_model=UserProfile)
def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Initialize achievements if needed
    initialize_default_achievements(db)
    
    # Update stats and check for new achievements
    new_achievements = check_and_award_achievements(current_user.id, db)
    
    # Get user stats
    stats = db.query(UserStats).filter(UserStats.user_id == current_user.id).first()
    if not stats:
        stats = UserStats(user_id=current_user.id)
        db.add(stats)
        db.commit()
    
    # Get recent achievements (last 10)
    recent_achievements = (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == current_user.id)
        .order_by(UserAchievement.earned_at.desc())
        .limit(10)
        .all()
    )
    
    # Get badge progress for unearned achievements
    all_achievements = db.query(Achievement).all()
    earned_achievement_ids = {ua.achievement_id for ua in recent_achievements}
    
    badge_progress = []
    for achievement in all_achievements:
        is_earned = achievement.id in earned_achievement_ids
        progress = 0.0
        progress_text = "Not started"
        
        if not is_earned:
            try:
                if achievement.requirement_type == "total_runs":
                    current_value = stats.total_runs or 0
                    progress = min(1.0, current_value / achievement.requirement_value)
                    progress_text = f"{current_value}/{int(achievement.requirement_value)} runs"
                elif achievement.requirement_type == "total_distance":
                    current_value = stats.total_distance_km or 0
                    progress = min(1.0, current_value / achievement.requirement_value)
                    progress_text = f"{current_value:.1f}/{achievement.requirement_value:.0f} km"
                elif achievement.requirement_type == "single_run_distance":
                    current_value = stats.longest_run_km or 0
                    progress = min(1.0, current_value / achievement.requirement_value)
                    progress_text = f"{current_value:.1f}/{achievement.requirement_value:.0f} km best"
            except (ZeroDivisionError, TypeError):
                progress = 0.0
                progress_text = "Not started"
        else:
            progress = 1.0
            progress_text = "Completed!"
        
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