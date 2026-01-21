from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WeatherDataBase(BaseModel):
    latitude: float
    longitude: float
    temperature: float
    feels_like: float
    humidity: int
    wind_speed: float
    wind_direction: int
    weather_condition: str
    weather_description: str
    weather_icon: str
    visibility: Optional[float] = None
    uv_index: Optional[float] = None
    pressure: Optional[float] = None
    location_name: Optional[str] = None

class WeatherDataCreate(WeatherDataBase):
    run_id: Optional[str] = None

class WeatherData(WeatherDataBase):
    id: int
    run_id: Optional[str] = None
    recorded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class WeatherAlertBase(BaseModel):
    alert_type: str  # temperature, rain, wind, etc.
    condition: str   # above, below, equals
    threshold_value: float
    message: Optional[str] = None

class WeatherAlertCreate(WeatherAlertBase):
    pass

class WeatherAlert(WeatherAlertBase):
    id: int
    user_id: str
    is_active: str
    created_at: datetime

    class Config:
        from_attributes = True

class CurrentWeatherResponse(BaseModel):
    weather: WeatherData
    recommendation: dict
    alerts: list[str] = []

class WeatherForecast(BaseModel):
    date: str
    temperature_min: float
    temperature_max: float
    weather_condition: str
    weather_description: str
    weather_icon: str
    precipitation_probability: float
    wind_speed: float

class WeatherHistoryResponse(BaseModel):
    weather_data: list[WeatherData]
    average_temperature: float
    most_common_condition: str
    total_records: int