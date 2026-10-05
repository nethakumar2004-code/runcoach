from collections import defaultdict
from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.run import CompletedRun
from app.models.user import User
from app.schemas.dashboard import (
    DashboardSummary,
    WeeklyLoads,
    DailyLoad,
)
from app.dependencies import get_current_user
from app.services.training import rolling_loads, run_load
from app.timeutils import utcnow

router = APIRouter()


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    loads = rolling_loads(db, current_user.id, utcnow())
    return DashboardSummary(
        total_distance_7d=loads["distance_7d"],
        total_load_7d=loads["load_7d"],
        avg_daily_load_28d=loads["avg_daily_load_28d"],
        acwr=loads["acwr"],
    )


@router.get("/weekly_loads", response_model=WeeklyLoads)
def get_weekly_loads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start = (utcnow() - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
    runs = (
        db.query(CompletedRun)
        .filter(
            CompletedRun.user_id == current_user.id,
            CompletedRun.start_datetime >= start,
        )
        .all()
    )

    # Summed in Python with the shared run_load(): the old SQL used `rpe or 0`, which
    # doesn't work on a column and dropped every run saved without an RPE
    distance_by_day = defaultdict(float)
    load_by_day = defaultdict(float)
    for r in runs:
        day = r.start_datetime.date()
        distance_by_day[day] += r.distance_km
        load_by_day[day] += run_load(r)

    days = [
        DailyLoad(day=day, distance_km=distance_by_day[day], load=load_by_day[day])
        for day in sorted(distance_by_day)
    ]
    return WeeklyLoads(days=days)
