"""Training load maths shared by runs, dashboard and analytics, so every screen shows the same numbers."""
from datetime import datetime, timedelta
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.models.run import CompletedRun

# Runs saved without an RPE are treated as moderate effort. This must match everywhere,
# otherwise the dashboard and the saved run disagree (one used 5, the other 0).
DEFAULT_RPE = 5

# Speed badges, best pace and pace records only count runs at least this long:
# pace over a few metres of GPS is noise.
MIN_DISTANCE_FOR_PACE_KM = 1.0


def session_load(duration_sec: float, rpe: Optional[int]) -> float:
    """Session RPE load = minutes x RPE."""
    return (duration_sec / 60.0) * (rpe or DEFAULT_RPE)


def run_load(run: CompletedRun) -> float:
    if run.training_load is not None:
        return float(run.training_load)
    return session_load(run.duration_sec, run.rpe)


def total_load(runs: Iterable[CompletedRun]) -> float:
    return float(sum(run_load(r) for r in runs))


def rolling_loads(db: Session, user_id: str, now: datetime) -> dict:
    """7-day load, 28-day average daily load and the acute:chronic workload ratio."""
    runs_28d = (
        db.query(CompletedRun)
        .filter(CompletedRun.user_id == user_id, CompletedRun.start_datetime >= now - timedelta(days=28))
        .all()
    )
    runs_7d = [r for r in runs_28d if r.start_datetime >= now - timedelta(days=7)]

    load_7d = total_load(runs_7d)
    load_28d = total_load(runs_28d)
    avg_daily_load_28d = load_28d / 28.0

    # ACWR compares this week with the last 4 weeks. With less than 4 weeks of history the
    # "chronic" part is mostly empty and the ratio is meaningless (a brand-new user got 4.0 = "danger").
    first_run = (
        db.query(CompletedRun.start_datetime)
        .filter(CompletedRun.user_id == user_id)
        .order_by(CompletedRun.start_datetime.asc())
        .first()
    )
    has_enough_history = first_run is not None and first_run[0] <= now - timedelta(days=28)
    acwr = load_7d / (avg_daily_load_28d * 7.0) if has_enough_history and avg_daily_load_28d > 0 else None

    return {
        "load_7d": load_7d,
        "load_28d": load_28d,
        "avg_daily_load_28d": avg_daily_load_28d,
        "acwr": acwr,
        "distance_7d": float(sum(r.distance_km for r in runs_7d)),
    }
