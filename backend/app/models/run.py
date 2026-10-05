from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db import Base

class CompletedRun(Base):
    __tablename__ = "completed_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    planned_workout_id = Column(String, nullable=True)  # Remove foreign key constraint for now

    start_datetime = Column(DateTime, nullable=False)
    distance_km = Column(Float, nullable=False)
    duration_sec = Column(Integer, nullable=False)
    avg_pace_s_per_km = Column(Float, nullable=False)
    avg_hr = Column(Integer, nullable=True)
    rpe = Column(Integer, nullable=True)  # Rate of Perceived Exertion (1-10)
    avg_cadence_spm = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Training metrics
    training_load = Column(Float, nullable=True)  # Calculated training stress
    calories_burned = Column(Integer, nullable=True)
    
    # GPS tracking data
    gps_route = Column(JSON, nullable=True)  # Array of {lat, lng, timestamp, elevation?, speed?}
    start_location = Column(JSON, nullable=True)  # {lat, lng, address?}
    end_location = Column(JSON, nullable=True)  # {lat, lng, address?}
    elevation_gain_m = Column(Float, nullable=True)
    max_speed_kmh = Column(Float, nullable=True)
    
    # Heart rate data
    hr_data = Column(JSON, nullable=True)  # Array of {bpm, timestamp, zone}
    max_hr = Column(Integer, nullable=True)
    min_hr = Column(Integer, nullable=True)
    hr_zones = Column(JSON, nullable=True)  # Time spent in each zone
    
    # Pace analysis
    pace_data = Column(JSON, nullable=True)  # Array of {km, pace_s_per_km, elevation}
    splits = Column(JSON, nullable=True)  # Array of split times per km
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Note: Relationships commented out to avoid circular import issues
    # weather_data = relationship("WeatherData", back_populates="run", uselist=False)
