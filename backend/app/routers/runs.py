import logging
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.run import CompletedRun
from app.models.user import User
from app.schemas.run import RunCreate, RunResponse, RunListItem, RunDetail
from app.dependencies import get_current_user
from app.services.achievements import check_and_award_achievements
from app.services.social import record_activity, update_challenge_progress
from app.services.training import rolling_loads, run_load, session_load
from app.timeutils import utcnow

logger = logging.getLogger(__name__)

router = APIRouter()

# Slower than 30 min/km means the watch was left running; cap it so averages aren't wrecked
MAX_PACE_S_PER_KM = 1800


def calculate_calories_burned(
    distance_km: float,
    duration_sec: int,
    weight_kg: float = 70.0,  # Default weight if not provided
    avg_hr: int = None,
    elevation_gain_m: float = None
) -> int:
    """
    Calculate calories burned during running using multiple methods for accuracy.
    
    Uses a combination of:
    1. MET (Metabolic Equivalent) values based on pace
    2. Heart rate if available
    3. Elevation adjustment
    """
    
    # Convert duration to hours
    duration_hours = duration_sec / 3600
    
    # Calculate pace in min/km
    pace_min_per_km = (duration_sec / 60) / distance_km if distance_km > 0 else 10
    
    # MET values based on running pace (from research data)
    if pace_min_per_km <= 3.5:  # Very fast (< 3:30/km)
        met_value = 19.0
    elif pace_min_per_km <= 4.0:  # Fast (3:30-4:00/km)
        met_value = 15.3
    elif pace_min_per_km <= 4.5:  # Moderate-fast (4:00-4:30/km)
        met_value = 12.8
    elif pace_min_per_km <= 5.0:  # Moderate (4:30-5:00/km)
        met_value = 11.0
    elif pace_min_per_km <= 5.5:  # Easy-moderate (5:00-5:30/km)
        met_value = 9.8
    elif pace_min_per_km <= 6.0:  # Easy (5:30-6:00/km)
        met_value = 8.3
    elif pace_min_per_km <= 7.0:  # Slow jog (6:00-7:00/km)
        met_value = 7.0
    else:  # Very slow (> 7:00/km)
        met_value = 6.0
    
    # Base calorie calculation: METs × weight (kg) × time (hours)
    base_calories = met_value * weight_kg * duration_hours
    
    # Heart rate adjustment (if available)
    if avg_hr and avg_hr > 0:
        # Estimate max HR (220 - age, assuming age 30 if not available)
        estimated_max_hr = 190  # Conservative estimate
        hr_intensity = min(avg_hr / estimated_max_hr, 1.0)
        
        # Adjust calories based on HR intensity
        hr_multiplier = 0.8 + (hr_intensity * 0.4)  # Range: 0.8 to 1.2
        base_calories *= hr_multiplier
    
    # Elevation adjustment (climbing burns more calories)
    if elevation_gain_m and elevation_gain_m > 0:
        # Add ~0.5 calories per kg per meter of elevation gain
        elevation_calories = (elevation_gain_m * weight_kg * 0.5)
        base_calories += elevation_calories
    
    # Round to nearest integer
    return max(1, int(round(base_calories)))


@router.get("/ping")
def ping():
    return {"status": "ok"}


@router.post("/", response_model=RunResponse)
def create_run(
    run_in: RunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Distance, duration, RPE, heart rate and pace ranges are already validated by RunCreate
    avg_pace = min(run_in.duration_sec / run_in.distance_km, MAX_PACE_S_PER_KM)
    load = session_load(run_in.duration_sec, run_in.rpe)

    gps_route_json = [
        {
            "lat": point.lat,
            "lng": point.lng,
            "timestamp": point.timestamp.isoformat(),
            "elevation": point.elevation,
            "speed": point.speed
        }
        for point in run_in.gps_route
    ]
    start_location_json = run_in.start_location.model_dump() if run_in.start_location else None
    end_location_json = run_in.end_location.model_dump() if run_in.end_location else None
    hr_data_json = [
        {"bpm": point.bpm, "timestamp": point.timestamp.isoformat(), "zone": point.zone}
        for point in run_in.hr_data
    ]

    avg_hr = max_hr = min_hr = hr_zones = None
    if run_in.hr_data:
        bpms = [point.bpm for point in run_in.hr_data]
        avg_hr = int(sum(bpms) / len(bpms))
        max_hr = max(bpms)
        min_hr = min(bpms)
        hr_zones = {}
        for point in run_in.hr_data:  # samples per zone
            hr_zones[point.zone] = hr_zones.get(point.zone, 0) + 1

    calories_burned = calculate_calories_burned(
        distance_km=run_in.distance_km,
        duration_sec=run_in.duration_sec,
        weight_kg=run_in.weight_kg or 70.0,
        avg_hr=avg_hr or run_in.avg_hr,
        elevation_gain_m=run_in.elevation_gain_m
    )

    db_run = CompletedRun(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        planned_workout_id=run_in.planned_workout_id,
        start_datetime=run_in.start_datetime,
        distance_km=run_in.distance_km,
        duration_sec=run_in.duration_sec,
        avg_pace_s_per_km=avg_pace,
        avg_hr=avg_hr or run_in.avg_hr,
        rpe=run_in.rpe,
        avg_cadence_spm=run_in.avg_cadence_spm,
        notes=run_in.notes or "",
        training_load=load,
        calories_burned=calories_burned,
        gps_route=gps_route_json,
        start_location=start_location_json,
        end_location=end_location_json,
        elevation_gain_m=run_in.elevation_gain_m,
        max_speed_kmh=run_in.max_speed_kmh,
        hr_data=hr_data_json,
        max_hr=max_hr or run_in.max_hr,
        min_hr=min_hr or run_in.min_hr,
        hr_zones=hr_zones,
        splits=[split.model_dump() for split in run_in.splits],
    )
    db.add(db_run)
    record_activity(db, current_user.id, "run_completed", {
        "run_id": db_run.id,
        "distance_km": round(run_in.distance_km, 2),
        "duration_sec": run_in.duration_sec,
        "avg_pace_s_per_km": round(avg_pace, 1),
    })
    db.commit()
    logger.info("Run %s saved for user %s (%.2f km)", db_run.id, current_user.id, run_in.distance_km)

    # The run is saved at this point. Achievements and challenges are extras: if they fail,
    # log it and still tell the app the save worked, so it doesn't retry and save the run twice.
    new_achievements = []
    try:
        update_challenge_progress(db, current_user.id)
        new_achievements = check_and_award_achievements(current_user.id, db)
    except Exception:
        db.rollback()
        logger.exception("Post-run processing failed for run %s", db_run.id)

    loads = rolling_loads(db, current_user.id, max(utcnow(), run_in.start_datetime))
    return RunResponse(
        run_id=db_run.id,
        training_load=load,
        load_7_day=loads["load_7d"],
        load_28_day=loads["load_28d"],
        calories_burned=calories_burned,
        new_achievements=[a.name for a in new_achievements],
    )


@router.get("/", response_model=List[RunListItem])
def list_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    runs = (
        db.query(CompletedRun)
        .filter(CompletedRun.user_id == current_user.id)
        .order_by(CompletedRun.start_datetime.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for r in runs:
        start_location = None
        if r.start_location:
            start_location = {
                "lat": r.start_location["lat"],
                "lng": r.start_location["lng"],
                "address": r.start_location.get("address")
            }

        result.append({
            "id": r.id,
            "start_datetime": r.start_datetime,
            "distance_km": r.distance_km,
            "duration_sec": r.duration_sec,
            "training_load": run_load(r),
            "calories_burned": r.calories_burned,
            "start_location": start_location,
            "avg_hr": r.avg_hr
        })

    return result


@router.get("/{run_id}", response_model=RunDetail)
def get_run_detail(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = (
        db.query(CompletedRun)
        .filter(CompletedRun.id == run_id, CompletedRun.user_id == current_user.id)
        .first()
    )
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    # Convert JSON data back to proper format
    gps_route = []
    if run.gps_route:
        gps_route = [
            {
                "lat": point["lat"],
                "lng": point["lng"],
                "timestamp": datetime.fromisoformat(point["timestamp"]),
                "elevation": point.get("elevation"),
                "speed": point.get("speed")
            }
            for point in run.gps_route
        ]
    
    # Convert HR data back to proper format
    hr_data = []
    if run.hr_data:
        hr_data = [
            {
                "bpm": point["bpm"],
                "timestamp": datetime.fromisoformat(point["timestamp"]),
                "zone": point["zone"]
            }
            for point in run.hr_data
        ]
    
    start_location = None
    if run.start_location:
        start_location = {
            "lat": run.start_location["lat"],
            "lng": run.start_location["lng"],
            "address": run.start_location.get("address")
        }
    
    end_location = None
    if run.end_location:
        end_location = {
            "lat": run.end_location["lat"],
            "lng": run.end_location["lng"],
            "address": run.end_location.get("address")
        }
    
    return RunDetail(
        id=run.id,
        start_datetime=run.start_datetime,
        distance_km=run.distance_km,
        duration_sec=run.duration_sec,
        avg_pace_s_per_km=run.avg_pace_s_per_km,
        calories_burned=run.calories_burned,  # Include calories
        avg_hr=run.avg_hr,
        rpe=run.rpe,
        avg_cadence_spm=run.avg_cadence_spm,
        notes=run.notes,
        gps_route=gps_route,
        start_location=start_location,
        end_location=end_location,
        elevation_gain_m=run.elevation_gain_m,
        max_speed_kmh=run.max_speed_kmh,
        hr_data=hr_data,
        max_hr=run.max_hr,
        min_hr=run.min_hr,
        hr_zones=run.hr_zones,
    )
