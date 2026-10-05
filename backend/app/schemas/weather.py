from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from datetime import datetime

# Weather fields an alert can watch, plus the shorthand names the app may send
ALERT_FIELD_ALIASES = {
    "temperature": "temperature",
    "temp": "temperature",
    "feels_like": "feels_like",
    "humidity": "humidity",
    "wind_speed": "wind_speed",
    "wind": "wind_speed",
    "visibility": "visibility",
    "uv_index": "uv_index",
    "uv": "uv_index",
    "pressure": "pressure",
}

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
    id: Optional[int] = None  # None for live lookups, which are no longer stored on every request
    run_id: Optional[str] = None
    recorded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class WeatherAlertBase(BaseModel):
    alert_type: str  # temperature, feels_like, humidity, wind_speed, visibility, uv_index, pressure
    condition: str   # above, below, equals
    threshold_value: float
    message: Optional[str] = None

class WeatherAlertCreate(WeatherAlertBase):
    condition: Literal["above", "below", "equals"]
    message: Optional[str] = Field(default=None, max_length=500)

    @field_validator("alert_type")
    @classmethod
    def check_alert_type(cls, value: str) -> str:
        field = ALERT_FIELD_ALIASES.get(value.strip().lower())
        if not field:
            allowed = ", ".join(sorted(set(ALERT_FIELD_ALIASES.values())))
            raise ValueError(f"alert_type must be one of: {allowed}")
        return field

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
    is_mock: bool = False  # True when no OPENWEATHER_API_KEY is set and sample data is returned

class WeatherForecast(BaseModel):
    date: str
    temperature_min: float
    temperature_max: float
    weather_condition: str
    weather_description: str
    weather_icon: str
    precipitation_probability: float
    wind_speed: float
    is_mock: bool = False

class WeatherHistoryResponse(BaseModel):
    weather_data: list[WeatherData]
    average_temperature: float
    most_common_condition: str
    total_records: int