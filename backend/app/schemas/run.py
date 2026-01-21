from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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

class Split(BaseModel):
    km: int
    distance_km: float
    duration_sec: int
    pace_sec_per_km: int

class RunCreate(BaseModel):
    start_datetime: datetime
    distance_km: float
    duration_sec: int
    avg_hr: int | None = None
    rpe: int | None = None
    avg_cadence_spm: int | None = None
    notes: str | None = None
    planned_workout_id: str | None = None
    splits: List[Split] = []
    
    # User data for calorie calculation
    weight_kg: Optional[float] = None  # User's weight for calorie calculation
    
    # GPS tracking data
    gps_route: List[GPSPoint] = []
    start_location: Optional[Location] = None
    end_location: Optional[Location] = None
    elevation_gain_m: Optional[float] = None
    max_speed_kmh: Optional[float] = None
    
    # Heart rate data
    hr_data: List[HeartRatePoint] = []
    max_hr: Optional[int] = None
    min_hr: Optional[int] = None
    hr_zones: Optional[dict] = None  # Time spent in each zone

class RunResponse(BaseModel):
    run_id: str
    training_load: float
    load_7_day: float
    load_28_day: float
    calories_burned: int  # Add calories to response

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
