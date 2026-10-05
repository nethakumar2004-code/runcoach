"""Achievement and user-stats logic, used both when a run is saved and when the profile is opened."""
from datetime import date, timedelta
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.achievement import Achievement, UserAchievement, UserStats
from app.models.run import CompletedRun
from app.services.social import record_activity
from app.services.training import MIN_DISTANCE_FOR_PACE_KM
from app.timeutils import utcnow

DEFAULT_ACHIEVEMENTS = [
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


def initialize_default_achievements(db: Session):
    """Create the default achievements if the table is empty."""
    if db.query(Achievement).first():
        return
    for ach_data in DEFAULT_ACHIEVEMENTS:
        db.add(Achievement(**ach_data))
    db.commit()


def calculate_streaks(run_dates: List[date], today: date) -> Tuple[int, int]:
    """Return (current_streak, longest_streak) in days.

    The current streak counts back from today, or from yesterday if the user hasn't run yet today.
    Days are UTC days.
    """
    days = sorted(set(run_dates))
    if not days:
        return 0, 0

    longest = run = 1
    for previous, current in zip(days, days[1:]):
        run = run + 1 if current - previous == timedelta(days=1) else 1
        longest = max(longest, run)

    current_streak = 0
    if days[-1] >= today - timedelta(days=1):
        current_streak = 1
        for previous, current in zip(reversed(days[:-1]), reversed(days[1:])):
            if current - previous != timedelta(days=1):
                break
            current_streak += 1

    return current_streak, longest


def level_for_points(points: int) -> int:
    return max(1, (points or 0) // 100 + 1)


def update_user_stats(user_id: str, db: Session) -> UserStats:
    """Recalculate user statistics from their runs (does not commit)."""
    stats = db.query(UserStats).filter(UserStats.user_id == user_id).first()
    if not stats:
        stats = UserStats(user_id=user_id, total_points=0)
        db.add(stats)
    if stats.total_points is None:
        stats.total_points = 0

    runs = db.query(CompletedRun).filter(CompletedRun.user_id == user_id).all()
    now = utcnow()
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    stats.total_runs = len(runs)
    stats.total_distance_km = sum(r.distance_km for r in runs)
    stats.total_time_minutes = sum(r.duration_sec / 60 for r in runs)
    stats.longest_run_km = max((r.distance_km for r in runs), default=0.0)

    # Only runs long enough for the pace to mean something count towards best pace / speed badges
    paces = [
        r.avg_pace_s_per_km for r in runs
        if r.distance_km >= MIN_DISTANCE_FOR_PACE_KM and r.avg_pace_s_per_km and r.avg_pace_s_per_km > 0
    ]
    stats.best_pace_per_km = min(paces) if paces else None

    stats.current_streak_days, stats.longest_streak_days = calculate_streaks(
        [r.start_datetime.date() for r in runs], now.date()
    )
    stats.this_week_distance = sum(r.distance_km for r in runs if r.start_datetime >= week_start)
    stats.this_month_distance = sum(r.distance_km for r in runs if r.start_datetime >= month_start)

    stats.level = level_for_points(stats.total_points)
    return stats


def _is_earned(achievement: Achievement, stats: UserStats) -> bool:
    kind = achievement.requirement_type
    if kind == "total_runs":
        return (stats.total_runs or 0) >= achievement.requirement_value
    if kind == "total_distance":
        return (stats.total_distance_km or 0) >= achievement.requirement_value
    if kind == "single_run_distance":
        return (stats.longest_run_km or 0) >= achievement.requirement_value
    if kind == "best_pace":
        return stats.best_pace_per_km is not None and stats.best_pace_per_km <= achievement.requirement_value
    if kind == "streak_days":
        return (stats.longest_streak_days or 0) >= achievement.requirement_value
    return False


def check_and_award_achievements(user_id: str, db: Session) -> List[Achievement]:
    """Update stats, award any newly earned achievements, and commit. Returns the new achievements."""
    initialize_default_achievements(db)
    stats = update_user_stats(user_id, db)
    earned_ids = {
        a_id for (a_id,) in db.query(UserAchievement.achievement_id).filter(UserAchievement.user_id == user_id)
    }

    new_achievements = []
    for achievement in db.query(Achievement).all():
        if achievement.id in earned_ids or not _is_earned(achievement, stats):
            continue
        db.add(UserAchievement(user_id=user_id, achievement_id=achievement.id, progress=1.0))
        stats.total_points = (stats.total_points or 0) + (achievement.points or 0)
        record_activity(db, user_id, "achievement_earned", {
            "achievement_id": achievement.id,
            "name": achievement.name,
            "icon": achievement.icon,
            "rarity": achievement.rarity,
            "points": achievement.points,
        })
        new_achievements.append(achievement)

    # Level is computed after the points are added, so it doesn't lag one check behind
    stats.level = level_for_points(stats.total_points)
    db.commit()
    return new_achievements


def _format_pace(seconds_per_km: float) -> str:
    return f"{int(seconds_per_km // 60)}:{int(seconds_per_km % 60):02d}/km"


def badge_progress_for(achievement: Achievement, stats: UserStats) -> Tuple[float, str]:
    """Progress (0-1) and a short label for an achievement the user hasn't earned yet."""
    target = achievement.requirement_value or 0
    kind = achievement.requirement_type

    if kind == "best_pace":
        best = stats.best_pace_per_km
        if not best:
            return 0.0, f"Target {_format_pace(target)} (runs of 1 km+)"
        return min(1.0, target / best), f"Best {_format_pace(best)} / target {_format_pace(target)}"

    if target <= 0:
        return 0.0, "Not started"

    if kind == "total_runs":
        current = stats.total_runs or 0
        return min(1.0, current / target), f"{current}/{int(target)} runs"
    if kind == "total_distance":
        current = stats.total_distance_km or 0
        return min(1.0, current / target), f"{current:.1f}/{target:.0f} km"
    if kind == "single_run_distance":
        current = stats.longest_run_km or 0
        return min(1.0, current / target), f"{current:.1f}/{target:.1f} km best"
    if kind == "streak_days":
        current = stats.current_streak_days or 0
        return min(1.0, current / target), f"{current}/{int(target)} day streak"
    return 0.0, "Not started"
