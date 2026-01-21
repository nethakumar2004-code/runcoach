from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.db import get_db
from app.models.user import User
from app.models.run import CompletedRun
from app.dependencies import get_current_user

router = APIRouter()

@router.get("/advanced")
def get_advanced_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get advanced analytics including pace zones, trends, and race predictions with real-time metrics"""
    
    # Get user's runs from last 90 days for analysis
    ninety_days_ago = datetime.utcnow() - timedelta(days=90)
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
    week_ago = datetime.utcnow() - timedelta(days=7)
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
    avg_pace = sum(run.avg_pace_s_per_km for run in runs) / len(runs)
    
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
        weekly_data[week_key]['total_load'] += run.training_load
    
    # Calculate trends for last 8 weeks
    trends = []
    for week_key in sorted(weekly_data.keys())[-8:]:
        data = weekly_data[week_key]
        if data['runs']:
            avg_pace = sum(run.avg_pace_s_per_km for run in data['runs']) / len(data['runs'])
            trends.append({
                "date": week_key,
                "avg_pace": avg_pace,
                "distance": data['total_distance'],
                "training_load": data['total_load']
            })
    
    return trends

def calculate_race_predictions(runs: List[CompletedRun]):
    """Calculate race time predictions based on recent performance"""
    if len(runs) < 3:
        return []
    
    # Get runs from last 30 days for predictions
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_runs = [run for run in runs if run.start_datetime >= thirty_days_ago]
    
    if len(recent_runs) < 3:
        return []
    
    # Calculate average pace from recent runs
    avg_pace = sum(run.avg_pace_s_per_km for run in recent_runs) / len(recent_runs)
    
    # Race distance predictions with pace adjustments
    race_distances = [
        {"distance": "5K", "km": 5.0, "pace_factor": 0.95},  # 5% faster than training pace
        {"distance": "10K", "km": 10.0, "pace_factor": 0.97}, # 3% faster than training pace
        {"distance": "Half Marathon", "km": 21.1, "pace_factor": 1.05}, # 5% slower than training pace
        {"distance": "Marathon", "km": 42.2, "pace_factor": 1.15}  # 15% slower than training pace
    ]
    
    predictions = []
    for race in race_distances:
        predicted_pace = avg_pace * race["pace_factor"]
        predicted_time_sec = predicted_pace * race["km"]
        
        # Calculate confidence based on training data
        confidence = min(len(recent_runs) / 10.0, 1.0)  # Max confidence with 10+ runs
        
        # Format time
        hours = int(predicted_time_sec // 3600)
        minutes = int((predicted_time_sec % 3600) // 60)
        seconds = int(predicted_time_sec % 60)
        
        if hours > 0:
            time_str = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            time_str = f"{minutes}:{seconds:02d}"
        
        predictions.append({
            "distance": race["distance"],
            "predicted_time": time_str,
            "confidence": confidence,
            "based_on_runs": len(recent_runs)
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
    
    # Find fastest 5K and 10K (approximate distances)
    fastest_5k = None
    fastest_10k = None
    
    for run in runs:
        # 5K (4.5-5.5km range)
        if 4.5 <= run.distance_km <= 5.5:
            if fastest_5k is None or run.duration_sec < fastest_5k:
                fastest_5k = run.duration_sec
        
        # 10K (9.5-10.5km range)
        if 9.5 <= run.distance_km <= 10.5:
            if fastest_10k is None or run.duration_sec < fastest_10k:
                fastest_10k = run.duration_sec
    
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
        "best_pace": min(run.avg_pace_s_per_km for run in runs)
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
    avg_pace = sum(run.avg_pace_s_per_km for run in weekly_runs) / len(weekly_runs)
    
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
    month_ago = datetime.utcnow() - timedelta(days=30)
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