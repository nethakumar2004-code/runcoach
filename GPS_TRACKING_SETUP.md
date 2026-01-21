# GPS Tracking Setup Guide

Your RunCoach app now has Strava-like GPS tracking! Here's what's been implemented:

## 🎯 Features Added

### Backend Features:
- **GPS Route Storage** - Stores complete GPS tracks with lat/lng coordinates
- **Location Data** - Captures start/end locations with optional addresses
- **Elevation Tracking** - Records elevation gain during runs
- **Speed Tracking** - Captures max speed and real-time pace
- **Enhanced API** - New endpoints for GPS-enabled runs

### Mobile Features:
- **Real-time GPS Tracking** - Live location tracking during runs
- **Interactive Maps** - Visual route display with start/end markers
- **Live Stats** - Real-time distance, pace, and time tracking
- **Route Visualization** - Strava-like polyline routes on maps
- **GPS Accuracy Indicator** - Shows GPS signal quality
- **Run History with Maps** - View past runs with their routes

## 🚀 How to Use

### 1. Start GPS Tracking
- Open the app and tap **"🗺️ GPS Track Run"** button
- Grant location permissions when prompted
- Wait for GPS to get a good signal (green indicator)
- Tap **"Start Run"** to begin tracking

### 2. During Your Run
- Watch live stats: time, distance, current pace
- See your route being drawn on the map in real-time
- GPS accuracy indicator shows signal quality
- Pause/resume as needed

### 3. Save Your Run
- Tap **"Stop"** when finished
- Review your route on the map
- Add RPE (Rate of Perceived Exertion) 1-10
- Add optional notes
- Tap **"Save Run"** to store with GPS data

### 4. View Past Runs
- Runs with GPS data show a 🗺️ icon
- Tap any run to see detailed view with route map
- View elevation gain, max speed, and full GPS track

## 📱 Navigation

- **Home Screen**: Two run options - basic tracking or GPS tracking
- **GPS Track Run**: Full-featured GPS tracking screen
- **Run History**: Tap any run to see details and map
- **Run Details**: Complete run analysis with interactive map

## 🔧 Technical Details

### GPS Data Stored:
- **Route Points**: Latitude, longitude, timestamp, elevation, speed
- **Start/End Locations**: Precise start and finish coordinates
- **Metrics**: Total elevation gain, maximum speed
- **Accuracy**: GPS signal quality tracking

### Map Features:
- **Route Polyline**: Red line showing your exact path
- **Start Marker**: Green pin at run start
- **End Marker**: Red pin at run finish
- **Auto-zoom**: Map automatically fits your route
- **Real-time Updates**: Live tracking during runs

## 🛠️ Setup Requirements

### Already Installed:
- `expo-location` - GPS tracking
- `react-native-maps` - Map visualization
- Location permissions configured in app.json

### Database:
- New GPS columns added to completed_runs table
- Backward compatible with existing runs

## 🎉 Ready to Use!

Your app now has professional GPS tracking like Strava! Users can:
- Track runs with precise GPS routes
- View beautiful route maps
- Analyze elevation and speed data
- Build a complete running history with visual routes

Just restart your backend and mobile app to start using the new GPS features!