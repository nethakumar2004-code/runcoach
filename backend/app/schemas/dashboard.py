from datetime import date
from typing import List
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_distance_7d: float
    total_load_7d: float
    avg_daily_load_28d: float
    acwr: float | None


class DailyLoad(BaseModel):
    day: date
    distance_km: float
    load: float


class WeeklyLoads(BaseModel):
    days: List[DailyLoad]
