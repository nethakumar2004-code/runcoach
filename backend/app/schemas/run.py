from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from datetime import datetime

from app.timeutils import to_naive_utc

# Faster than 2:00/km over 100 m or more is beyond any human (world records are ~2:20/km) - it's GPS error or cheating
FASTEST_REALISTIC_PACE_S_PER_KM = 120
MAX_TRACK_POINTS = 50_000  # ~14 hours at one point per second

# Response models stay lenient so runs that are already stored always load
class GPSPoint(BaseModel):
    lat: float
    lng: float
    timestamp: datetime
    elevation: Optional[float] = None
    speed: Optional[float] = None  # km/h

class HeartRatePoint(BaseModel):
    bpm: int
    timestamp: datetime
    zone: str  # 'resting', 'fat-burn', 'aerobic', 'anaerobic', 'max'

class Location(BaseModel):
    lat: float
    lng: float
    address: Optional[str] = None

# Input models: what the phone sends when saving a run
class GPSPointIn(GPSPoint):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)

    @field_validator("speed")
    @classmethod
    def unknown_speed(cls, value: Optional[float]) -> Optional[float]:
        # iOS reports speed -1 m/s (-3.6 km/h) when it doesn't know - that's "unknown", not an error
        return value if value is not None and value >= 0 else None

class HeartRatePointIn(HeartRatePoint):
    bpm: int = Field(ge=0, le=250)  # 0 = sensor dropout

class LocationIn(Location):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)

class Split(BaseModel):
    km: int
    distance_km: float
    duration_sec: int
    pace_sec_per_km: int

class RunCreate(BaseModel):
    start_datetime: datetime
    distance_km: float = Field(gt=0, le=500)
    duration_sec: int = Field(gt=0, le=7 * 24 * 3600)
    avg_hr: Optional[int] = None
    rpe: Optional[int] = Field(default=None, ge=0, le=10)  # 0 = not set
    avg_cadence_spm: Optional[int] = None
    notes: Optional[str] = Field(default=None, max_length=5000)
    planned_workout_id: Optional[str] = None
    splits: List[Split] = Field(default=[], max_length=1000)

    # User data for calorie calculation
    weight_kg: Optional[float] = None

    # GPS tracking data
    gps_route: List[GPSPointIn] = Field(default=[], max_length=MAX_TRACK_POINTS)
    start_location: Optional[LocationIn] = None
    end_location: Optional[LocationIn] = None
    elevation_gain_m: Optional[float] = None
    max_speed_kmh: Optional[float] = None

    # Heart rate data
    hr_data: List[HeartRatePointIn] = Field(default=[], max_length=MAX_TRACK_POINTS)
    max_hr: Optional[int] = None
    min_hr: Optional[int] = None
    hr_zones: Optional[dict] = None  # Time spent in each zone

    @field_validator("rpe")
    @classmethod
    def unset_rpe(cls, value: Optional[int]) -> Optional[int]:
        return value or None

    @field_validator("avg_hr", "max_hr", "min_hr")
    @classmethod
    def plausible_heart_rate(cls, value: Optional[int]) -> Optional[int]:
        # Sensor readings outside 20-250 bpm (e.g. 0 with no strap) mean "no data", not a bad run
        return value if value is not None and 20 <= value <= 250 else None

    @field_validator("avg_cadence_spm")
    @classmethod
    def plausible_cadence(cls, value: Optional[int]) -> Optional[int]:
        return value if value is not None and 0 < value <= 300 else None

    @field_validator("weight_kg")
    @classmethod
    def plausible_weight(cls, value: Optional[float]) -> Optional[float]:
        return value if value is not None and 20 <= value <= 400 else None  # falls back to 70 kg

    @field_validator("max_speed_kmh")
    @classmethod
    def plausible_speed(cls, value: Optional[float]) -> Optional[float]:
        return value if value is not None and 0 <= value <= 100 else None

    @field_validator("elevation_gain_m")
    @classmethod
    def plausible_elevation_gain(cls, value: Optional[float]) -> Optional[float]:
        return value if value is not None and 0 <= value <= 20000 else None

    @field_validator("start_datetime")
    @classmethod
    def normalise_start(cls, value: datetime) -> datetime:
        return to_naive_utc(value)

    @model_validator(mode="after")
    def check_realistic_pace(self):
        if self.distance_km >= 0.1:
            pace = self.duration_sec / self.distance_km
            if pace < FASTEST_REALISTIC_PACE_S_PER_KM:
                raise ValueError(
                    "Unrealistic pace (faster than 2:00/km). This is usually a GPS error - please check the run."
                )
        return self

class RunResponse(BaseModel):
    run_id: str
    training_load: float
    load_7_day: float
    load_28_day: float
    calories_burned: int  # Add calories to response
    new_achievements: List[str] = []  # names of achievements unlocked by this run

class RunListItem(BaseModel):
    id: str  # UUID stored as string in DB
    start_datetime: datetime
    distance_km: float
    duration_sec: int
    training_load: float
    calories_burned: Optional[int] = None  # Add calories
    start_location: Optional[Location] = None
    avg_hr: Optional[int] = None

class RunDetail(BaseModel):
    id: str
    start_datetime: datetime
    distance_km: float
    duration_sec: int
    avg_pace_s_per_km: float
    calories_burned: Optional[int] = None  # Add calories
    avg_hr: Optional[int] = None
    rpe: Optional[int] = None
    avg_cadence_spm: Optional[int] = None
    notes: Optional[str] = None

    # GPS data for map display
    gps_route: List[GPSPoint] = []
    start_location: Optional[Location] = None
    end_location: Optional[Location] = None
    elevation_gain_m: Optional[float] = None
    max_speed_kmh: Optional[float] = None

    # Heart rate data
    hr_data: List[HeartRatePoint] = []
    max_hr: Optional[int] = None
    min_hr: Optional[int] = None
    hr_zones: Optional[dict] = None
