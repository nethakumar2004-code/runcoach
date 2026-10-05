# Smart Training Plans Feature

## Overview
The Smart Training Plans feature provides users with structured, progressive training programs to help them achieve their running goals. The feature includes both frontend components and backend API support.

## Features Implemented

### Frontend (React Native)
- **TrainingPlan Component** (`mobile/runcoach-mobile/components/TrainingPlan.tsx`)
  - Browse available training plans
  - Enroll in training plans
  - View weekly workout schedules
  - Navigate between weeks
  - Mark workouts as completed
  - Track progress statistics

- **Training Plan Screen** (`mobile/runcoach-mobile/app/training-plan.tsx`)
  - Dedicated screen for training plan management

- **Dashboard Integration**
  - Added "Training Plan" button to main dashboard navigation

### Backend (FastAPI)
- **Database Models** (`backend/app/models/training_plan.py`)
  - `TrainingPlan`: Core training plan information
  - `TrainingWorkout`: Individual workout details
  - `UserTrainingPlan`: User enrollment and progress tracking
  - `UserWorkoutCompletion`: Workout completion records

- **API Schemas** (`backend/app/schemas/training_plan.py`)
  - Request/response models for all training plan operations
  - Proper validation and type safety

- **API Endpoints** (`backend/app/routers/training_plans.py`)
  - `GET /training-plans/` - List available plans
  - `GET /training-plans/{id}` - Get specific plan details
  - `POST /training-plans/enroll/{id}` - Enroll in a plan
  - `GET /training-plans/my/current` - Get user's active plan
  - `GET /training-plans/my/progress` - Get progress statistics
  - `GET /training-plans/my/week/{week}` - Get weekly workouts
  - `POST /training-plans/workouts/{id}/complete` - Mark workout complete
  - `PUT /training-plans/my/week` - Update current week

### Sample Data
- **Population Script** (`backend/populate_training_plans.py`)
  - Creates sample training plans for 5K, 10K, and Half Marathon
  - Different difficulty levels (beginner, intermediate, advanced)
  - Structured weekly workout schedules

## Training Plan Types

### 5K Training Plan (Beginner)
- Duration: 8 weeks
- Focus: Building base fitness for first 5K
- Workout types: Easy runs, intervals, tempo, long runs, rest days

### 10K Training Plan (Intermediate)
- Duration: 12 weeks
- Focus: Building endurance for 10K distance
- More structured tempo and interval work

### Half Marathon Plan (Advanced)
- Duration: 16 weeks
- Focus: Advanced training for 21.1K distance
- Complex workout structures with pace-specific training

## Workout Types

1. **Easy Runs**: Conversational pace, aerobic base building
2. **Tempo Runs**: Comfortably hard pace, lactate threshold training
3. **Interval Training**: High-intensity repeats with recovery
4. **Long Runs**: Extended duration for endurance building
5. **Rest Days**: Recovery and cross-training

## Technical Features

### Authentication Integration
- Requires user login to enroll and track progress
- Secure API endpoints with JWT token validation

### Progress Tracking
- Week-by-week navigation
- Workout completion status
- Progress statistics and analytics

### Responsive Design
- Clean, intuitive mobile interface
- Color-coded workout types
- Progress visualization

## Usage Flow

1. **Browse Plans**: User views available training plans
2. **Enroll**: User selects and enrolls in a plan
3. **Weekly View**: User sees current week's workouts
4. **Complete Workouts**: User marks workouts as completed
5. **Progress**: User tracks overall progress and advancement

## Future Enhancements

- Adaptive plan adjustments based on performance
- Custom plan creation
- Integration with GPS tracking for automatic completion
- Heart rate zone training
- Recovery recommendations
- Social sharing of progress
- Coach feedback and modifications

## Files Created/Modified

### New Files
- `mobile/runcoach-mobile/components/TrainingPlan.tsx`
- `mobile/runcoach-mobile/app/training-plan.tsx`
- `backend/app/models/training_plan.py`
- `backend/app/schemas/training_plan.py`
- `backend/app/routers/training_plans.py`
- `backend/app/models/base.py`
- `backend/populate_training_plans.py`

### Modified Files
- `mobile/runcoach-mobile/app/(tabs)/index.tsx` - Added navigation button
- `backend/app/models/user.py` - Added training plan relationship
- `backend/app/main.py` - Added training plans router

## Setup Instructions

1. **Backend Setup**:
   ```bash
   # Run the population script to add sample data
   cd backend
   python populate_training_plans.py
   ```

2. **Frontend Usage**:
   - Navigate to the main dashboard
   - Tap "📋 Training Plan" button
   - Browse and enroll in a training plan
   - Follow weekly workout schedules

The Smart Training Plans feature is now fully integrated and ready for use!