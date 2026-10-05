import logging
from typing import List
from datetime import timedelta, timezone, datetime

import requests
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app import config
from app.db import get_db
from app.models.run import CompletedRun
from app.models.user import User
from app.models.weather import WeatherData, WeatherAlert
from app.schemas.weather import (
    WeatherData as WeatherDataSchema,
    WeatherDataCreate,
    WeatherAlert as WeatherAlertSchema,
    WeatherAlertCreate,
    CurrentWeatherResponse,
    WeatherForecast,
    WeatherHistoryResponse
)
from app.dependencies import get_current_user
from app.timeutils import utcnow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weather", tags=["weather"])

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5"
REQUEST_TIMEOUT_SECONDS = 5


def _weather_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Weather service is unavailable right now. Please try again later.",
    )


def _fetch(endpoint: str, lat: float, lon: float) -> dict:
    """Call OpenWeatherMap. Raises 503 instead of silently returning made-up weather."""
    try:
        response = requests.get(
            f"{OPENWEATHER_URL}/{endpoint}",
            params={"lat": lat, "lon": lon, "appid": config.OPENWEATHER_API_KEY, "units": "metric"},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        logger.exception("OpenWeatherMap %s request failed", endpoint)
        raise _weather_unavailable()


# Plain `def` (not `async def`): FastAPI runs these in a thread pool, so a slow
# weather API no longer blocks every other request on the server.
@router.get("/current", response_model=CurrentWeatherResponse)
def get_current_weather(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current weather for a location"""
    is_mock = config.OPENWEATHER_API_KEY is None
    if is_mock:
        weather_data = create_mock_weather_data(lat, lon)
    else:
        data = _fetch("weather", lat, lon)
        try:
            weather_data = WeatherDataCreate(
                latitude=lat,
                longitude=lon,
                temperature=data["main"]["temp"],
                feels_like=data["main"]["feels_like"],
                humidity=data["main"]["humidity"],
                wind_speed=data.get("wind", {}).get("speed", 0),
                wind_direction=data.get("wind", {}).get("deg", 0),
                weather_condition=data["weather"][0]["main"],
                weather_description=data["weather"][0]["description"],
                weather_icon=data["weather"][0]["icon"],
                visibility=data.get("visibility", 10000) / 1000,  # Convert to km
                pressure=data["main"].get("pressure"),
                location_name=data.get("name") or "Unknown Location"
            )
        except (KeyError, IndexError, TypeError, ValueError):
            logger.exception("Unexpected OpenWeatherMap response")
            raise _weather_unavailable()

    now = utcnow()
    recommendation = generate_running_recommendation(weather_data)
    if is_mock:
        recommendation["message"] = "Sample weather - live weather is not configured on the server"

    return CurrentWeatherResponse(
        weather=WeatherDataSchema(**weather_data.model_dump(), recorded_at=now, created_at=now),
        recommendation=recommendation,
        alerts=check_weather_alerts(db, current_user.id, weather_data),
        is_mock=is_mock,
    )

def create_mock_weather_data(lat: float, lon: float) -> WeatherDataCreate:
    """Clearly labelled sample data for development without an API key"""
    return WeatherDataCreate(
        latitude=lat,
        longitude=lon,
        temperature=22.0,
        feels_like=24.0,
        humidity=65,
        wind_speed=3.2,
        wind_direction=180,
        weather_condition="Clear",
        weather_description="sample data (no API key)",
        weather_icon="01d",
        visibility=10.0,
        uv_index=5.0,
        pressure=1013.25,
        location_name="Sample weather (no API key)"
    )

def generate_running_recommendation(weather: WeatherDataCreate) -> dict:
    """Generate running recommendations based on weather conditions"""
    temp = weather.temperature
    humidity = weather.humidity
    wind_speed = weather.wind_speed
    condition = weather.weather_condition.lower()
    
    recommendations = []
    level = "good"
    color = "#4CAF50"
    
    # Temperature recommendations
    if temp < 0:
        recommendations.append("Very cold - dress in layers and warm up indoors")
        level = "caution"
        color = "#2196F3"
    elif temp < 10:
        recommendations.append("Cool weather - great for running!")
        level = "excellent"
        color = "#4CAF50"
    elif temp < 20:
        recommendations.append("Perfect running temperature!")
        level = "excellent"
        color = "#4CAF50"
    elif temp < 25:
        recommendations.append("Warm - stay hydrated")
        level = "good"
        color = "#FF9800"
    elif temp < 30:
        recommendations.append("Hot - consider running early morning or evening")
        level = "caution"
        color = "#FF5722"
    else:
        recommendations.append("Very hot - consider indoor exercise")
        level = "warning"
        color = "#F44336"
    
    # Humidity recommendations
    if humidity > 80:
        recommendations.append("High humidity - take frequent breaks")
        if level == "excellent":
            level = "good"
    elif humidity > 60:
        recommendations.append("Moderate humidity - stay hydrated")
    
    # Wind recommendations
    if wind_speed > 10:
        recommendations.append("Strong winds - be cautious of debris")
        if level in ["excellent", "good"]:
            level = "caution"
    elif wind_speed > 5:
        recommendations.append("Moderate winds - may affect pace")
    
    # Weather condition recommendations
    if condition in ["rain", "drizzle"]:
        recommendations.append("Rainy conditions - wear appropriate gear")
        level = "caution"
        color = "#2196F3"
    elif condition == "thunderstorm":
        recommendations.append("Thunderstorm - avoid outdoor running")
        level = "warning"
        color = "#F44336"
    elif condition == "snow":
        recommendations.append("Snowy conditions - watch for slippery surfaces")
        level = "caution"
        color = "#2196F3"
    elif condition in ["mist", "fog"]:
        recommendations.append("Low visibility - wear bright colors")
        level = "caution"
    
    return {
        "level": level,
        "color": color,
        "message": " • ".join(recommendations[:2]),  # Limit to 2 main recommendations
        "all_recommendations": recommendations
    }

def check_weather_alerts(db: Session, user_id: str, weather: WeatherDataCreate) -> List[str]:
    """Check if weather conditions trigger any user alerts"""
    alerts = db.query(WeatherAlert).filter(
        WeatherAlert.user_id == user_id,
        WeatherAlert.is_active == "true"
    ).all()
    
    triggered_alerts = []
    
    for alert in alerts:
        value = getattr(weather, alert.alert_type, None)
        if value is None:
            continue
            
        if alert.condition == "above" and value > alert.threshold_value:
            triggered_alerts.append(alert.message or f"{alert.alert_type} is above {alert.threshold_value}")
        elif alert.condition == "below" and value < alert.threshold_value:
            triggered_alerts.append(alert.message or f"{alert.alert_type} is below {alert.threshold_value}")
        elif alert.condition == "equals" and abs(value - alert.threshold_value) < 0.1:
            triggered_alerts.append(alert.message or f"{alert.alert_type} equals {alert.threshold_value}")
    
    return triggered_alerts

@router.get("/forecast", response_model=List[WeatherForecast])
def get_weather_forecast(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    days: int = Query(5, ge=1, le=5, description="Number of days (1-5)")
):
    """Get weather forecast for the next few days"""
    if config.OPENWEATHER_API_KEY is None:
        return create_mock_forecast(days)

    data = _fetch("forecast", lat, lon)
    try:
        # Group the 3-hourly entries by the location's local date, not the UTC date
        offset = timedelta(seconds=data.get("city", {}).get("timezone", 0))
        daily_data = {}
        for item in data["list"]:
            local_date = (datetime.fromtimestamp(item["dt"], tz=timezone.utc) + offset).strftime("%Y-%m-%d")
            daily_data.setdefault(local_date, []).append(item)

        forecast = []
        for date, day_items in list(daily_data.items())[:days]:
            temps = [item["main"]["temp"] for item in day_items]
            conditions = [item["weather"][0] for item in day_items]

            condition_counts = {}
            for cond in conditions:
                condition_counts[cond["main"]] = condition_counts.get(cond["main"], 0) + 1
            most_common = max(condition_counts.items(), key=lambda x: x[1])[0]
            representative = next(c for c in conditions if c["main"] == most_common)

            forecast.append(WeatherForecast(
                date=date,
                temperature_min=min(temps),
                temperature_max=max(temps),
                weather_condition=most_common,
                weather_description=representative["description"],
                weather_icon=representative["icon"],
                # Worst case of the day, not just the first 3-hour slot
                precipitation_probability=max(item.get("pop", 0) for item in day_items) * 100,
                wind_speed=max(item.get("wind", {}).get("speed", 0) for item in day_items)
            ))
        return forecast
    except (KeyError, IndexError, TypeError, ValueError):
        logger.exception("Unexpected OpenWeatherMap forecast response")
        raise _weather_unavailable()

def create_mock_forecast(days: int) -> List[WeatherForecast]:
    """Clearly labelled sample forecast for development without an API key"""
    base_date = utcnow()
    return [
        WeatherForecast(
            date=(base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            temperature_min=18 + i,
            temperature_max=25 + i,
            weather_condition="Clear",
            weather_description="sample data (no API key)",
            weather_icon="01d",
            precipitation_probability=10 + i * 5,
            wind_speed=3.0 + i * 0.5,
            is_mock=True,
        )
        for i in range(days)
    ]

@router.post("/alerts", response_model=WeatherAlertSchema)
def create_weather_alert(
    alert: WeatherAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a weather alert for the user"""
    db_alert = WeatherAlert(
        user_id=current_user.id,
        **alert.model_dump()
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

@router.get("/alerts", response_model=List[WeatherAlertSchema])
def get_weather_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's weather alerts"""
    alerts = db.query(WeatherAlert).filter(
        WeatherAlert.user_id == current_user.id
    ).all()
    return alerts

@router.delete("/alerts/{alert_id}")
def delete_weather_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a weather alert"""
    alert = db.query(WeatherAlert).filter(
        WeatherAlert.id == alert_id,
        WeatherAlert.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Weather alert not found"
        )
    
    db.delete(alert)
    db.commit()
    return {"message": "Weather alert deleted"}

@router.get("/history", response_model=WeatherHistoryResponse)
def get_weather_history(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get weather history for the current user's runs"""
    start_date = utcnow() - timedelta(days=days)

    # Join through the runs table so users only ever see weather attached to their OWN runs
    weather_data = db.query(WeatherData).join(
        CompletedRun, WeatherData.run_id == CompletedRun.id
    ).filter(
        CompletedRun.user_id == current_user.id,
        WeatherData.created_at >= start_date,
    ).all()

    if not weather_data:
        return WeatherHistoryResponse(
            weather_data=[],
            average_temperature=0,
            most_common_condition="Unknown",
            total_records=0
        )

    temperatures = [w.temperature for w in weather_data]
    condition_counts = {}
    for w in weather_data:
        condition_counts[w.weather_condition] = condition_counts.get(w.weather_condition, 0) + 1

    return WeatherHistoryResponse(
        weather_data=weather_data,
        average_temperature=round(sum(temperatures) / len(temperatures), 1),
        most_common_condition=max(condition_counts.items(), key=lambda x: x[1])[0],
        total_records=len(weather_data)
    )
