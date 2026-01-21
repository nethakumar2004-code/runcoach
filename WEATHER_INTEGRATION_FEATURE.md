# Weather Integration Feature 🌤️

## Overview
The Weather Integration feature provides real-time weather data, forecasts, and weather-based running recommendations to help users plan their runs effectively. The feature includes both frontend components and backend API support with OpenWeatherMap integration.

## Features Implemented

### Frontend (React Native)
- **WeatherWidget Component** (`mobile/runcoach-mobile/components/WeatherWidget.tsx`)
  - Real-time weather display with temperature, humidity, wind
  - Running recommendations based on conditions
  - Compact and full display modes
  - Weather icons and condition descriptions
  - Location-based weather data

- **Weather Screen** (`mobile/runcoach-mobile/app/weather.tsx`)
  - Detailed weather information
  - 5-day weather forecast
  - Weather alerts management
  - Running tips for different conditions
  - Pull-to-refresh functionality

- **Dashboard Integration**
  - Weather widget embedded in main dashboard
  - "🌤️ Weather" button for detailed weather screen

### Backend (FastAPI)
- **Database Models** (`backend/app/models/weather.py`)
  - `WeatherData`: Store weather conditions for runs
  - `WeatherAlert`: User-configurable weather notifications

- **API Schemas** (`backend/app/schemas/weather.py`)
  - Request/response models for weather operations
  - Forecast and alert data structures

- **API Endpoints** (`backend/app/routers/weather.py`)
  - `GET /weather/current` - Current weather with recommendations
  - `GET /weather/forecast` - 5-day weather forecast
  - `POST /weather/alerts` - Create weather alerts
  - `GET /weather/alerts` - Get user's weather alerts
  - `DELETE /weather/alerts/{id}` - Delete weather alert
  - `GET /weather/history` - Weather history for past runs

### Weather Data Integration
- **OpenWeatherMap API Integration**
  - Real-time weather data
  - 5-day forecast
  - Fallback to mock data for development
  - Location-based weather retrieval

## Weather Features

### Current Weather Display
- **Temperature**: Current and "feels like" temperature
- **Weather Conditions**: Clear, cloudy, rainy, etc. with icons
- **Wind Information**: Speed and direction
- **Humidity**: Percentage humidity levels
- **Visibility**: Current visibility in kilometers
- **Location**: Current location name

### Running Recommendations
Intelligent recommendations based on weather conditions:

#### Temperature-Based Recommendations
- **Very Cold (< 0°C)**: "Dress in layers, warm up indoors"
- **Cool (0-10°C)**: "Great for running!"
- **Perfect (10-20°C)**: "Perfect running weather!"
- **Warm (20-25°C)**: "Stay hydrated"
- **Hot (25-30°C)**: "Run early morning or evening"
- **Very Hot (> 30°C)**: "Consider indoor exercise"

#### Condition-Based Recommendations
- **Rain/Drizzle**: "Wear appropriate gear"
- **Thunderstorm**: "Avoid outdoor running"
- **Snow**: "Watch for slippery surfaces"
- **Fog/Mist**: "Wear bright colors"
- **High Humidity**: "Take frequent breaks"
- **Strong Winds**: "Be cautious of debris"

### Weather Forecast
- **5-Day Forecast**: Daily temperature ranges and conditions
- **Precipitation Probability**: Rain chance percentage
- **Wind Speed**: Daily wind conditions
- **Weather Icons**: Visual condition indicators

### Weather Alerts System
- **Custom Alerts**: User-configurable weather notifications
- **Alert Types**: Temperature, rain, wind, UV index
- **Conditions**: Above, below, or equal to thresholds
- **Custom Messages**: Personalized alert messages

### Weather History
- **Run Weather Tracking**: Weather conditions during past runs
- **Statistics**: Average temperature, most common conditions
- **Historical Analysis**: Weather patterns for training analysis

## Technical Implementation

### Location Services
- Uses Expo Location API for GPS coordinates
- Requests foreground location permissions
- Balanced accuracy for battery efficiency

### API Integration
- OpenWeatherMap API for real-time data
- Graceful fallback to mock data
- Error handling and retry logic
- Caching for performance

### Data Storage
- Weather data stored with run records
- User alert preferences saved
- Historical weather analysis

### UI/UX Features
- **Weather Icons**: Condition-specific Ionicons
- **Color Coding**: Temperature and condition-based colors
- **Responsive Design**: Compact and full display modes
- **Pull-to-Refresh**: Easy data updates
- **Loading States**: Smooth user experience

## Weather Running Tips

### Hot Weather (> 25°C)
- Run during cooler hours (early morning/evening)
- Increase hydration before, during, and after
- Wear light-colored, breathable clothing
- Reduce intensity and take breaks

### Cold Weather (< 10°C)
- Layer clothing for temperature regulation
- Warm up indoors before starting
- Protect extremities (hands, feet, head)
- Stay visible with reflective gear

### Rainy Conditions
- Wear moisture-wicking, water-resistant gear
- Choose well-lit, safe routes
- Be extra cautious of slippery surfaces
- Consider treadmill as alternative

### Windy Conditions
- Start running into the wind, return with tailwind
- Be aware of debris and obstacles
- Adjust pace expectations
- Consider sheltered routes

## Setup Instructions

### Backend Setup
1. **Get OpenWeatherMap API Key**:
   ```bash
   # Sign up at https://openweathermap.org/api
   # Set environment variable
   export OPENWEATHER_API_KEY="your_api_key_here"
   ```

2. **Install Dependencies**:
   ```bash
   pip install requests  # For API calls
   ```

### Frontend Usage
1. **Location Permissions**: App requests location access
2. **Weather Widget**: Automatically loads on dashboard
3. **Detailed Weather**: Tap "🌤️ Weather" button
4. **Alerts**: Set up custom weather notifications
5. **Forecast**: View 5-day weather outlook

## API Configuration

### Environment Variables
```bash
OPENWEATHER_API_KEY=your_openweather_api_key
```

### Mock Data Fallback
- Automatic fallback when API unavailable
- Development-friendly mock weather data
- Consistent data structure for testing

## Future Enhancements

### Advanced Weather Features
- **UV Index Tracking**: Sun exposure recommendations
- **Air Quality Index**: Pollution level warnings
- **Severe Weather Alerts**: Storm and extreme weather warnings
- **Hourly Forecasts**: More detailed timing recommendations

### Smart Recommendations
- **Training Plan Integration**: Weather-adjusted workout suggestions
- **Route Recommendations**: Weather-optimized running routes
- **Gear Suggestions**: Clothing and equipment recommendations
- **Hydration Reminders**: Temperature-based hydration alerts

### Historical Analysis
- **Weather Performance Correlation**: How weather affects running performance
- **Seasonal Trends**: Long-term weather pattern analysis
- **Personal Weather Preferences**: Learn user's preferred conditions

### Integration Features
- **Calendar Integration**: Weather-aware training scheduling
- **Wearable Sync**: Weather data on smartwatches
- **Social Sharing**: Share weather conditions with runs
- **Coach Integration**: Weather-informed training adjustments

## Files Created/Modified

### New Files
- `mobile/runcoach-mobile/components/WeatherWidget.tsx`
- `mobile/runcoach-mobile/app/weather.tsx`
- `backend/app/models/weather.py`
- `backend/app/schemas/weather.py`
- `backend/app/routers/weather.py`

### Modified Files
- `mobile/runcoach-mobile/app/(tabs)/index.tsx` - Added weather widget and navigation
- `backend/app/models/run.py` - Added weather relationship
- `backend/app/models/user.py` - Added weather alerts relationship
- `backend/app/main.py` - Added weather router

## Weather Data Structure

### Current Weather Response
```json
{
  "weather": {
    "temperature": 22,
    "feels_like": 24,
    "humidity": 65,
    "wind_speed": 3.2,
    "weather_condition": "Clear",
    "weather_description": "clear sky"
  },
  "recommendation": {
    "level": "excellent",
    "message": "Perfect running weather!",
    "color": "#4CAF50"
  },
  "alerts": []
}
```

### Forecast Data
```json
{
  "date": "2024-01-06",
  "temperature_min": 18,
  "temperature_max": 25,
  "weather_condition": "Clear",
  "precipitation_probability": 10,
  "wind_speed": 3.0
}
```

The Weather Integration feature is now fully implemented and ready to help users make informed decisions about their running activities based on current and forecasted weather conditions! 🌤️