from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import requests
import os

from app.db import get_db
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

router = APIRouter(prefix="/weather", tags=["weather"])

# You'll need to set this environment variable or get an API key from OpenWeatherMap
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "your_api_key_here")

@router.get("/current", response_model=CurrentWeatherResponse)
async def get_current_weather(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current weather for a location"""
    try:
        # Fetch from OpenWeatherMap API
        url = f"https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            # Fallback to mock data for development
            weather_data = create_mock_weather_data(lat, lon)
        else:
            data = response.json()
            weather_data = WeatherDataCreate(
                latitude=lat,
                longitude=lon,
                temperature=data["main"]["temp"],
                feels_like=data["main"]["feels_like"],
                humidity=data["main"]["humidity"],
                wind_speed=data["wind"]["speed"],
                wind_direction=data["wind"]["deg"],
                weather_condition=data["weather"][0]["main"],
                weather_description=data["weather"][0]["description"],
                weather_icon=data["weather"][0]["icon"],
                visibility=data.get("visibility", 10000) / 1000,  # Convert to km
                pressure=data["main"].get("pressure"),
                location_name=data.get("name", "Unknown Location")
            )
        
        # Save weather data to database
        db_weather = WeatherData(**weather_data.dict())
        db.add(db_weather)
        db.commit()
        db.refresh(db_weather)
        
        # Generate running recommendation
        recommendation = generate_running_recommendation(weather_data)
        
        # Check for user alerts
        alerts = check_weather_alerts(db, current_user.id, weather_data)
        
        return CurrentWeatherResponse(
            weather=db_weather,
            recommendation=recommendation,
            alerts=alerts
        )
        
    except Exception as e:
        # Fallback to mock data
        weather_data = create_mock_weather_data(lat, lon)
        db_weather = WeatherData(**weather_data.dict())
        db.add(db_weather)
        db.commit()
        db.refresh(db_weather)
        
        recommendation = generate_running_recommendation(weather_data)
        
        return CurrentWeatherResponse(
            weather=db_weather,
            recommendation=recommendation,
            alerts=[]
        )

def create_mock_weather_data(lat: float, lon: float) -> WeatherDataCreate:
    """Create mock weather data for development/fallback"""
    return WeatherDataCreate(
        latitude=lat,
        longitude=lon,
        temperature=22.0,
        feels_like=24.0,
        humidity=65,
        wind_speed=3.2,
        wind_direction=180,
        weather_condition="Clear",
        weather_description="clear sky",
        weather_icon="01d",
        visibility=10.0,
        uv_index=5.0,
        pressure=1013.25,
        location_name="Current Location"
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
async def get_weather_forecast(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    days: int = Query(5, description="Number of days (1-5)")
):
    """Get weather forecast for the next few days"""
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            # Return mock forecast data
            return create_mock_forecast(days)
        
        data = response.json()
        forecast = []
        
        # Group by day and get daily summary
        daily_data = {}
        for item in data["list"][:days * 8]:  # 8 forecasts per day (3-hour intervals)
            date = item["dt_txt"].split(" ")[0]
            if date not in daily_data:
                daily_data[date] = []
            daily_data[date].append(item)
        
        for date, day_items in list(daily_data.items())[:days]:
            temps = [item["main"]["temp"] for item in day_items]
            conditions = [item["weather"][0] for item in day_items]
            
            # Get most common condition
            condition_counts = {}
            for cond in conditions:
                key = cond["main"]
                condition_counts[key] = condition_counts.get(key, 0) + 1
            most_common = max(condition_counts.items(), key=lambda x: x[1])
            
            forecast.append(WeatherForecast(
                date=date,
                temperature_min=min(temps),
                temperature_max=max(temps),
                weather_condition=most_common[0],
                weather_description=conditions[0]["description"],
                weather_icon=conditions[0]["icon"],
                precipitation_probability=day_items[0].get("pop", 0) * 100,
                wind_speed=day_items[0]["wind"]["speed"]
            ))
        
        return forecast
        
    except Exception as e:
        return create_mock_forecast(days)

def create_mock_forecast(days: int) -> List[WeatherForecast]:
    """Create mock forecast data"""
    forecast = []
    base_date = datetime.now()
    
    for i in range(days):
        date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        forecast.append(WeatherForecast(
            date=date,
            temperature_min=18 + i,
            temperature_max=25 + i,
            weather_condition="Clear",
            weather_description="clear sky",
            weather_icon="01d",
            precipitation_probability=10 + i * 5,
            wind_speed=3.0 + i * 0.5
        ))
    
    return forecast

@router.post("/alerts", response_model=WeatherAlertSchema)
def create_weather_alert(
    alert: WeatherAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a weather alert for the user"""
    db_alert = WeatherAlert(
        user_id=current_user.id,
        **alert.dict()
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
    days: int = Query(30, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get weather history for user's runs"""
    start_date = datetime.now() - timedelta(days=days)
    
    weather_data = db.query(WeatherData).filter(
        WeatherData.created_at >= start_date,
        WeatherData.run_id.isnot(None)  # Only weather data associated with runs
    ).all()
    
    if not weather_data:
        return WeatherHistoryResponse(
            weather_data=[],
            average_temperature=0,
            most_common_condition="Unknown",
            total_records=0
        )
    
    # Calculate statistics
    temperatures = [w.temperature for w in weather_data]
    conditions = [w.weather_condition for w in weather_data]
    
    avg_temp = sum(temperatures) / len(temperatures)
    
    condition_counts = {}
    for condition in conditions:
        condition_counts[condition] = condition_counts.get(condition, 0) + 1
    most_common_condition = max(condition_counts.items(), key=lambda x: x[1])[0]
    
    return WeatherHistoryResponse(
        weather_data=weather_data,
        average_temperature=round(avg_temp, 1),
        most_common_condition=most_common_condition,
        total_records=len(weather_data)
    )