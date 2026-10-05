# 🏃‍♂️ RunCoach - Gaming Edition

A comprehensive running companion app with a sleek gaming-inspired interface, built with React Native (Expo) and FastAPI.

## ✨ Features

### 🎮 Gaming UI Experience
- **Dark Gaming Theme** with animated gradients and particle effects
- **Interactive Animations** with haptic feedback and smooth transitions
- **Glass-morphism Design** using BlurView components
- **Enhanced Visual Effects** including floating particles, glow effects, and sparkles
- **Gaming Color Palette** with cyan, pink, and blue accents

### 🏃‍♂️ Core Running Features
- **GPS Run Tracking** with real-time distance, pace, and time monitoring
- **Split Tracking** with automatic kilometer splits and pace analysis
- **Training Load Calculation** using RPE (Rate of Perceived Exertion)
- **Achievement System** with XP points and unlockable badges
- **Run History** with detailed statistics and GPS route visualization

### 📊 Analytics & Insights
- **Training Summary** with 7-day distance and load metrics
- **ACWR Monitoring** (Acute:Chronic Workload Ratio) for injury prevention
- **Weekly Charts** showing training load progression
- **Performance Analytics** with pace trends and distance tracking
- **Real-time Analytics** with live data updates

### 🌤️ Smart Features
- **Weather Integration** with running recommendations
- **Route Planning** with GPS-based route creation
- **Social Features** including friends, leaderboards, and activity sharing
- **Training Plans** with smart recommendations based on experience level
- **Audio Coaching** with voice guidance during runs

### 🎯 Gamification Elements
- **XP System** with level progression and rewards
- **Achievement Badges** for various running milestones
- **Challenge System** with weekly and monthly goals
- **Streak Tracking** for consistency motivation
- **Leaderboards** for competitive running

## 🚀 Tech Stack

### Frontend (Mobile)
- **React Native** with Expo framework
- **TypeScript** for type safety
- **Expo Router** for navigation
- **Expo Location** for GPS tracking
- **Expo Linear Gradient** for visual effects
- **Expo Blur** for glass-morphism effects
- **React Native Reanimated** for smooth animations
- **AsyncStorage** for local data persistence

### Backend (API)
- **FastAPI** with Python 3.9+
- **SQLAlchemy** ORM with SQLite database
- **Pydantic** for data validation
- **JWT Authentication** with secure token management
- **RESTful API** design with comprehensive endpoints
- **Weather API Integration** for real-time weather data

## 📱 Screenshots

### Gaming Dashboard
- Animated particle system with floating effects
- Interactive stat cards with haptic feedback
- XP progress bars with level badges
- Glass-morphism design elements

### Run Tracking
- Real-time GPS tracking with smooth animations
- Gaming-themed UI with gradient buttons
- Live statistics with enhanced typography
- Achievement notifications with celebration effects

### Analytics
- Enhanced charts with gaming aesthetics
- Interactive data visualization
- Performance insights with coaching tips
- Progress tracking with visual indicators

## 🛠️ Installation & Setup

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.9+
- Expo CLI (`npm install -g @expo/cli`)
- iOS Simulator or Android Emulator (or physical device)

### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (requirements-dev.txt also installs the test tools)
pip install -r requirements-dev.txt

# Optional: copy the example settings and fill them in
cp .env.example .env  # On Windows: copy .env.example .env

# Populate sample training plans (tables are created automatically)
python populate_training_plans.py

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The database is always `backend/dev.db`, no matter which folder you start the server from.

### Changing the database (migrations)
The server brings the database up to date automatically when it starts. When you change a model in `backend/app/models/`:
```bash
cd backend
alembic revision --autogenerate -m "add nickname to users"   # writes a file in migrations/versions/
```
Open the new file and check it does what you expect, then restart the server and commit the file together with the model change. If you forget, the `test_migrations_match_the_models` test fails and tells you.

### Running the tests
```bash
cd backend
pytest
```
Run the tests before every commit. Each bug that has been fixed has a test, so if one comes back you'll know straight away.

### Mobile App Setup
```bash
# Navigate to mobile directory
cd mobile/runcoach-mobile

# Install dependencies
npm install

# Start Expo development server
npx expo start

# Run on iOS simulator
npx expo run:ios

# Run on Android emulator
npx expo run:android
```

### Environment Configuration
All backend settings are optional and documented in `backend/.env.example`. The important ones:

| Setting | What it does |
|---|---|
| `SECRET_KEY` | Signs login tokens. If unset, a random key is generated once into `backend/.secret_key` (git-ignored). |
| `OPENWEATHER_API_KEY` | Live weather. Without it, weather endpoints return sample data marked `is_mock: true`. |
| `ADMIN_EMAILS` | Comma-separated emails allowed to create training plans through the API. |
| `RUNCOACH_DEV_MODE=1` | Enables the `dev-token` login used by the mobile debug screen and the `/training-plans` debug endpoints. **Never enable on a public server** - anyone could log in as the test user. |
| `DATABASE_URL` | Use a different database. |

**Mobile `.env`:**
```
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 🎮 Gaming Features Deep Dive

### Particle System
- 20 animated particles with physics-based movement
- Rotation and opacity animations
- Color-coded particles (cyan, pink, blue)
- Continuous regeneration for immersive experience

### Animation System
- **Fade-in animations** for smooth screen transitions
- **Pulse effects** for interactive elements
- **Float animations** for dynamic movement
- **Glow effects** for emphasis and attention
- **Sparkle animations** for celebration moments

### Interactive Elements
- **Haptic feedback** on button presses (iOS/Android)
- **Scale animations** for touch responses
- **Staggered entrance** animations for lists
- **Smooth transitions** between screens

### Visual Design
- **Dark gaming background** with gradient overlays
- **Glass-morphism cards** with blur effects
- **Gaming typography** with shadows and glows
- **Enhanced color palette** for better contrast
- **Modern UI patterns** following gaming design principles

## 📊 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user profile

### Runs & Tracking
- `GET /runs/` - Get user's run history
- `POST /runs/` - Save a new run
- `GET /runs/{run_id}` - Get specific run details
- `GET /dashboard` - Get training summary
- `GET /weekly_loads` - Get weekly training loads

### Social Features
- `GET /social/friends` - Get friends list
- `POST /social/friends/{user_id}` - Add friend
- `GET /social/feed` - Get activity feed
- `POST /social/share` - Share run activity

### Training & Analytics
- `GET /training_plans/` - Get available training plans
- `POST /training_plans/{plan_id}/enroll` - Enroll in training plan
- `GET /analytics/performance` - Get performance analytics
- `GET /achievements/profile` - Get user achievements

### Weather & Routes
- `GET /weather/current` - Get current weather
- `GET /weather/forecast` - Get weather forecast
- `POST /routes/` - Save a new route
- `GET /routes/` - Get saved routes

## 🔧 Development Scripts

### Backend Scripts
```bash
# Clean test data
python cleanup_test_data.py

# Add sample runs
python add_test_runs.py

# Test run creation
python test_run_creation.py

# Restart with fresh data
./restart-fresh.bat  # Windows
```

### Mobile Scripts
```bash
# Start development server
npm start

# Run on specific platform
npm run ios
npm run android

# Build for production
npm run build

# Type checking
npm run type-check
```

## 🎯 Key Gaming UI Components

### Enhanced Header
- User avatar with glow effects
- Level badge with pulse animation
- XP progress bar with gradient fill
- Theme toggle with smooth transitions

### Stat Cards
- Interactive touch responses
- Gradient backgrounds with shimmer effects
- Animated entrance with staggered timing
- Haptic feedback on interaction

### Action Buttons
- Gaming-themed gradients
- Scale animations on press
- Enhanced typography with shadows
- Consistent visual hierarchy

### Achievement System
- Celebration animations for new achievements
- Progress bars with smooth fills
- Icon-based achievement display
- Point system with XP rewards

## 🚀 Performance Optimizations

### Animation Performance
- Native driver usage for smooth 60fps animations
- Optimized particle system with efficient rendering
- Staggered animations to prevent frame drops
- Memory-efficient animation cleanup

### Data Management
- AsyncStorage for offline data persistence
- Efficient API caching strategies
- Optimized re-renders with React.memo
- Background data synchronization

### User Experience
- Haptic feedback for enhanced interaction
- Smooth transitions between screens
- Loading states with gaming aesthetics
- Error handling with user-friendly messages

## 📝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Expo Team** for the excellent React Native framework
- **FastAPI** for the high-performance Python web framework
- **React Native Reanimated** for smooth animation capabilities
- **OpenWeather API** for weather data integration
- **Gaming UI Inspiration** from modern mobile gaming interfaces

## 📞 Support

For support, email support@runcoach.app or join our Discord community.

---

**Built with ❤️ for runners who love gaming aesthetics**