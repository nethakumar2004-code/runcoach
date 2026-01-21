from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base

class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, ForeignKey("completed_runs.id"), nullable=True)  # Optional - can be standalone
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)  # Celsius
    feels_like = Column(Float, nullable=False)  # Celsius
    humidity = Column(Integer, nullable=False)  # Percentage
    wind_speed = Column(Float, nullable=False)  # m/s
    wind_direction = Column(Integer, nullable=False)  # Degrees
    weather_condition = Column(String(50), nullable=False)  # Clear, Clouds, Rain, etc.
    weather_description = Column(String(100), nullable=False)  # clear sky, light rain, etc.
    weather_icon = Column(String(10), nullable=False)  # OpenWeather icon code
    visibility = Column(Float, nullable=True)  # km
    uv_index = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)  # hPa
    location_name = Column(String(100), nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Note: Relationships commented out to avoid circular import issues
    # run = relationship("CompletedRun", back_populates="weather_data")

class WeatherAlert(Base):
    __tablename__ = "weather_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)  # temperature, rain, wind, etc.
    condition = Column(String(20), nullable=False)  # above, below, equals
    threshold_value = Column(Float, nullable=False)
    is_active = Column(String(10), default="true")  # true/false as string
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Note: Relationships commented out to avoid circular import issues  
    # user = relationship("User", back_populates="weather_alerts")