# app/api/dashboard.py
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
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

router = APIRouter()


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    start_7d = now - timedelta(days=7)
    start_28d = now - timedelta(days=28)

    runs_7d = (
        db.query(CompletedRun)
        .filter(
            CompletedRun.user_id == current_user.id,
            CompletedRun.start_datetime >= start_7d,
        )
        .all()
    )
    runs_28d = (
        db.query(CompletedRun)
        .filter(
            CompletedRun.user_id == current_user.id,
            CompletedRun.start_datetime >= start_28d,
        )
        .all()
    )

    def session_load(r: CompletedRun) -> float:
        return (r.duration_sec / 60.0) * (r.rpe or 0)

    total_distance_7d = float(sum(r.distance_km for r in runs_7d))
    total_load_7d = float(sum(session_load(r) for r in runs_7d))
    total_load_28d = float(sum(session_load(r) for r in runs_28d))
    avg_daily_load_28d = (
        total_load_28d / 28.0 if total_load_28d > 0 else 0.0
    )

    acwr = (
        total_load_7d / (avg_daily_load_28d * 7.0)
        if avg_daily_load_28d > 0
        else None
    )

    return DashboardSummary(
        total_distance_7d=total_distance_7d,
        total_load_7d=total_load_7d,
        avg_daily_load_28d=avg_daily_load_28d,
        acwr=acwr,
    )


@router.get("/weekly_loads", response_model=WeeklyLoads)
def get_weekly_loads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    start = now - timedelta(days=6)

    rows = (
        db.query(
            func.date(CompletedRun.start_datetime).label("day"),
            func.sum(CompletedRun.distance_km).label("distance_km"),
            func.sum(
                (CompletedRun.duration_sec / 60.0) * (CompletedRun.rpe or 0)
            ).label("load"),
        )
        .filter(
            CompletedRun.user_id == current_user.id,
            CompletedRun.start_datetime >= start,
        )
        .group_by(func.date(CompletedRun.start_datetime))
        .order_by("day")
        .all()
    )

    days = [
        DailyLoad(
            day=row.day,
            distance_km=float(row.distance_km or 0.0),
            load=float(row.load or 0.0),
        )
        for row in rows
    ]

    return WeeklyLoads(days=days)
