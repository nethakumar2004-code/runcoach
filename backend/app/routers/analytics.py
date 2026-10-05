from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import timedelta

from app.db import get_db
from app.models.user import User
from app.models.run import CompletedRun
from app.dependencies import get_current_user
from app.services.training import MIN_DISTANCE_FOR_PACE_KM, run_load
from app.timeutils import utcnow

router = APIRouter()


def average_pace(runs: List[CompletedRun]) -> float:
    """Total time / total distance. Averaging each run's pace instead lets a 1 km jog count as much as a 20 km run."""
    distance = sum(run.distance_km for run in runs)
    return sum(run.duration_sec for run in runs) / distance if distance > 0 else 0.0

@router.get("/advanced")
def get_advanced_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get advanced analytics including pace zones, trends, and race predictions with real-time metrics"""
    
    # Get user's runs from last 90 days for analysis
    ninety_days_ago = utcnow() - timedelta(days=90)
    recent_runs = db.query(CompletedRun).filter(
        CompletedRun.user_id == current_user.id,
        CompletedRun.start_datetime >= ninety_days_ago
    ).order_by(desc(CompletedRun.start_datetime)).all()
    
    if not recent_runs:
        return {
            "pace_zones": [],
            "performance_trends": [],
            "race_predictions": [],
            "personal_records": {
                "fastest_5k": None,
                "fastest_10k": None,
                "longest_run": 0,
                "best_pace": 0
            },
            "weekly_summary": {
                "total_distance": 0,
                "total_time": 0,
                "avg_pace": 0,
                "runs_count": 0
            },
            "live_metrics": {
                "recent_improvement": 0,
                "consistency_score": 0,
                "training_load_trend": "stable",
                "next_milestone": {
                    "type": "Start Running",
                    "target": 1,
                    "progress": 0
                },
                "weekly_goal_progress": 0,
                "monthly_goal_progress": 0
            }
        }
    
    # Calculate pace zones
    pace_zones = calculate_pace_zones(recent_runs)
    
    # Calculate performance trends (weekly averages)
    performance_trends = calculate_performance_trends(recent_runs)
    
    # Calculate race predictions
    race_predictions = calculate_race_predictions(recent_runs)
    
    # Calculate personal records
    all_runs = db.query(CompletedRun).filter(
        CompletedRun.user_id == current_user.id
    ).all()
    personal_records = calculate_personal_records(all_runs)
    
    # Calculate weekly summary
    week_ago = utcnow() - timedelta(days=7)
    weekly_runs = [run for run in recent_runs if run.start_datetime >= week_ago]
    weekly_summary = calculate_weekly_summary(weekly_runs)
    
    # Calculate live metrics
    live_metrics = calculate_live_metrics(recent_runs, weekly_runs, performance_trends)
    
    return {
        "pace_zones": pace_zones,
        "performance_trends": performance_trends,
        "race_predictions": race_predictions,
        "personal_records": personal_records,
        "weekly_summary": weekly_summary,
        "live_metrics": live_metrics
    }

def calculate_pace_zones(runs: List[CompletedRun]):
    """Calculate pace zone distribution"""
    if not runs:
        return []
    
    # Calculate average pace for zone boundaries
    avg_pace = average_pace(runs)
    
    # Define pace zones based on average pace (non-overlapping ranges)
    zones = [
        {
            "zone": "Fast",
            "min_pace": 0,
            "max_pace": avg_pace - 60,   # 1 min faster than avg
            "color": "#dc3545"
        },
        {
            "zone": "Tempo",
            "min_pace": avg_pace - 60,  # 1 min faster than avg
            "max_pace": avg_pace - 20,   # 20s faster than avg
            "color": "#fd7e14"
        },
        {
            "zone": "Moderate",
            "min_pace": avg_pace - 20,  # 20s faster than avg
            "max_pace": avg_pace + 20,   # 20s slower than avg
            "color": "#ffc107"
        },
        {
            "zone": "Easy",
            "min_pace": avg_pace + 20,  # 20s slower than avg
            "max_pace": avg_pace + 60,   # 1 min slower than avg
            "color": "#17a2b8"
        },
        {
            "zone": "Recovery",
            "min_pace": avg_pace + 60,  # 1 min slower than avg
            "max_pace": avg_pace + 120,  # 2 min slower than avg
            "color": "#28a745"
        }
    ]
    
    # Calculate percentage of time in each zone
    total_distance = sum(run.distance_km for run in runs)
    
    for zone in zones:
        zone_distance = 0
        for run in runs:
            # Check if run pace falls within this zone (inclusive of min, exclusive of max except for last zone)
            if zone == zones[-1]:  # Recovery zone (last zone)
                if run.avg_pace_s_per_km >= zone["min_pace"]:
                    zone_distance += run.distance_km
            else:
                if zone["min_pace"] <= run.avg_pace_s_per_km < zone["max_pace"]:
                    zone_distance += run.distance_km
        
        zone["percentage"] = (zone_distance / total_distance * 100) if total_distance > 0 else 0
    
    return zones

def calculate_performance_trends(runs: List[CompletedRun]):
    """Calculate weekly performance trends"""
    if len(runs) < 2:
        return []
    
    # Group runs by week
    weekly_data = {}
    for run in runs:
        # Get start of week (Monday)
        week_start = run.start_datetime - timedelta(days=run.start_datetime.weekday())
        week_key = week_start.strftime('%Y-%m-%d')
        
        if week_key not in weekly_data:
            weekly_data[week_key] = {
                'runs': [],
                'total_distance': 0,
                'total_time': 0,
                'total_load': 0
            }
        
        weekly_data[week_key]['runs'].append(run)
        weekly_data[week_key]['total_distance'] += run.distance_km
        weekly_data[week_key]['total_time'] += run.duration_sec
        weekly_data[week_key]['total_load'] += run_load(run)  # training_load can be NULL on old runs
    
    # Calculate trends for last 8 weeks
    trends = []
    for week_key in sorted(weekly_data.keys())[-8:]:
        data = weekly_data[week_key]
        if data['runs']:
            avg_pace = average_pace(data['runs'])
            trends.append({
                "date": week_key,
                "avg_pace": avg_pace,
                "distance": data['total_distance'],
                "training_load": data['total_load']
            })
    
    return trends

RIEGEL_EXPONENT = 1.06
MIN_PREDICTION_RUN_KM = 3.0


def riegel_time(known_time_sec: float, known_distance_km: float, target_distance_km: float) -> float:
    """Pete Riegel's endurance formula: T2 = T1 x (D2 / D1) ^ 1.06"""
    return known_time_sec * (target_distance_km / known_distance_km) ** RIEGEL_EXPONENT


def format_duration(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours > 0 else f"{minutes}:{secs:02d}"


def calculate_race_predictions(runs: List[CompletedRun]):
    """Predict race times from the best recent effort using the Riegel formula.

    Uses runs of 3 km+ from the last 30 days; for each race distance the fastest prediction wins,
    because a training run is at most as fast as race effort.
    """
    thirty_days_ago = utcnow() - timedelta(days=30)
    candidates = [
        run for run in runs
        if run.start_datetime >= thirty_days_ago and run.distance_km >= MIN_PREDICTION_RUN_KM and run.duration_sec > 0
    ]
    if not candidates:
        return []

    longest = max(run.distance_km for run in candidates)
    race_distances = [("5K", 5.0), ("10K", 10.0), ("Half Marathon", 21.0975), ("Marathon", 42.195)]

    predictions = []
    for name, km in race_distances:
        predicted = min(riegel_time(run.duration_sec, run.distance_km, km) for run in candidates)
        # More runs = more confidence; predicting far beyond your longest run = less confidence
        confidence = min(len(candidates) / 5.0, 1.0) * min(1.0, (longest * 2) / km)
        predictions.append({
            "distance": name,
            "predicted_time": format_duration(predicted),
            "confidence": round(confidence, 2),
            "based_on_runs": len(candidates)
        })

    return predictions

def calculate_personal_records(runs: List[CompletedRun]):
    """Calculate personal records"""
    if not runs:
        return {
            "fastest_5k": None,
            "fastest_10k": None,
            "longest_run": 0,
            "best_pace": 0
        }
    
    # A 5K record needs a run of (about) 5 km or more - a 4.5 km run's time is not a 5K time.
    # 2% tolerance for GPS under-measuring; time is the run's average pace over the full distance.
    def fastest_over(distance_km):
        times = [
            run.avg_pace_s_per_km * distance_km for run in runs
            if run.distance_km >= distance_km * 0.98 and run.avg_pace_s_per_km
        ]
        return min(times) if times else None

    fastest_5k = fastest_over(5.0)
    fastest_10k = fastest_over(10.0)
    pace_runs = [run.avg_pace_s_per_km for run in runs if run.distance_km >= MIN_DISTANCE_FOR_PACE_KM]

    # Format times
    def format_time(seconds):
        if seconds is None:
            return None
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    return {
        "fastest_5k": format_time(fastest_5k),
        "fastest_10k": format_time(fastest_10k),
        "longest_run": max(run.distance_km for run in runs),
        "best_pace": min(pace_runs) if pace_runs else 0
    }

def calculate_weekly_summary(weekly_runs: List[CompletedRun]):
    """Calculate summary for current week"""
    if not weekly_runs:
        return {
            "total_distance": 0,
            "total_time": 0,
            "avg_pace": 0,
            "runs_count": 0
        }
    
    total_distance = sum(run.distance_km for run in weekly_runs)
    total_time = sum(run.duration_sec for run in weekly_runs)
    avg_pace = average_pace(weekly_runs)
    
    return {
        "total_distance": total_distance,
        "total_time": total_time,
        "avg_pace": avg_pace,
        "runs_count": len(weekly_runs)
    }

def calculate_live_metrics(recent_runs: List[CompletedRun], weekly_runs: List[CompletedRun], performance_trends: List[dict]):
    """Calculate real-time performance metrics"""
    
    # Calculate recent improvement (last 2 weeks pace comparison)
    recent_improvement = 0
    if len(performance_trends) >= 2:
        recent = performance_trends[-1]
        previous = performance_trends[-2]
        if previous["avg_pace"] > 0:
            recent_improvement = ((previous["avg_pace"] - recent["avg_pace"]) / previous["avg_pace"]) * 100
    
    # Calculate consistency score (based on regular running)
    consistency_score = min(len(weekly_runs) * 25, 100)  # Max 4 runs per week = 100%
    
    # Determine training load trend
    training_load_trend = "stable"
    if len(performance_trends) >= 3:
        recent_loads = [t["training_load"] for t in performance_trends[-3:]]
        older_loads = [t["training_load"] for t in performance_trends[-6:-3]] if len(performance_trends) >= 6 else []
        
        if recent_loads and older_loads:
            avg_recent = sum(recent_loads) / len(recent_loads)
            avg_older = sum(older_loads) / len(older_loads)
            
            if avg_recent > avg_older * 1.1:
                training_load_trend = "increasing"
            elif avg_recent < avg_older * 0.9:
                training_load_trend = "decreasing"
    
    # Calculate next milestone
    weekly_distance = sum(run.distance_km for run in weekly_runs)
    weekly_runs_count = len(weekly_runs)
    next_milestone = get_next_milestone(weekly_distance, weekly_runs_count)
    
    # Calculate goal progress (assuming weekly goal of 20km and 4 runs)
    weekly_distance_goal = 20.0
    weekly_runs_goal = 4
    weekly_goal_progress = min((weekly_distance / weekly_distance_goal) * 100, 100) if weekly_distance_goal > 0 else 0
    
    # Calculate monthly progress
    month_ago = utcnow() - timedelta(days=30)
    monthly_runs = [run for run in recent_runs if run.start_datetime >= month_ago]
    monthly_distance = sum(run.distance_km for run in monthly_runs)
    monthly_distance_goal = 80.0  # 80km per month
    monthly_goal_progress = min((monthly_distance / monthly_distance_goal) * 100, 100) if monthly_distance_goal > 0 else 0
    
    return {
        "recent_improvement": recent_improvement,
        "consistency_score": consistency_score,
        "training_load_trend": training_load_trend,
        "next_milestone": next_milestone,
        "weekly_goal_progress": weekly_goal_progress,
        "monthly_goal_progress": monthly_goal_progress,
        "weekly_distance": weekly_distance,
        "monthly_distance": monthly_distance
    }

def get_next_milestone(weekly_distance: float, weekly_runs: int):
    """Calculate the next achievable milestone"""
    
    # Distance milestones (km per week)
    distance_milestones = [5, 10, 15, 20, 25, 30, 40, 50, 75, 100]
    next_distance_milestone = None
    for milestone in distance_milestones:
        if milestone > weekly_distance:
            next_distance_milestone = milestone
            break
    
    # Run count milestones (runs per week)
    run_milestones = [1, 2, 3, 4, 5, 6, 7]
    next_run_milestone = None
    for milestone in run_milestones:
        if milestone > weekly_runs:
            next_run_milestone = milestone
            break
    
    # Return the closest milestone
    if next_distance_milestone and next_run_milestone:
        distance_progress = weekly_distance / next_distance_milestone
        run_progress = weekly_runs / next_run_milestone
        
        if distance_progress > run_progress:
            return {
                "type": "Weekly Distance",
                "target": next_distance_milestone,
                "progress": (weekly_distance / next_distance_milestone) * 100,
                "unit": "km"
            }
        else:
            return {
                "type": "Weekly Runs",
                "target": next_run_milestone,
                "progress": (weekly_runs / next_run_milestone) * 100,
                "unit": "runs"
            }
    elif next_distance_milestone:
        return {
            "type": "Weekly Distance",
            "target": next_distance_milestone,
            "progress": (weekly_distance / next_distance_milestone) * 100,
            "unit": "km"
        }
    elif next_run_milestone:
        return {
            "type": "Weekly Runs",
            "target": next_run_milestone,
            "progress": (weekly_runs / next_run_milestone) * 100,
            "unit": "runs"
        }
    else:
        return {
            "type": "Keep Going!",
            "target": 100,
            "progress": 100,
            "unit": "%"
        }