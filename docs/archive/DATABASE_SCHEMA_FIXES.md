# Database Schema Fixes Applied

## Issues Found
The backend was failing to start due to foreign key reference errors in the new models.

### Error 1: Weather Model Foreign Key
**Error**: `Foreign key associated with column 'weather_data.run_id' could not find table 'runs'`

**Root Cause**: Weather model was referencing a non-existent table name.

### Error 2: Training Plan Model Data Type Mismatch
**Potential Issue**: User ID foreign key using wrong data type.

## Fixes Applied

### 1. Fixed Weather Model Foreign Key Reference
**File**: `backend/app/models/weather.py`

**Before:**
```python
run_id = Column(String, ForeignKey("runs.id"), nullable=True)
run = relationship("Run", back_populates="weather_data")
```

**After:**
```python
run_id = Column(String, ForeignKey("completed_runs.id"), nullable=True)
run = relationship("CompletedRun", back_populates="weather_data")
```

**Explanation**: 
- The actual table name is `completed_runs`, not `runs`
- The model class is `CompletedRun`, not `Run`

### 2. Fixed Training Plan Model User ID Data Type
**File**: `backend/app/models/training_plan.py`

**Before:**
```python
user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
```

**After:**
```python
user_id = Column(String, ForeignKey("users.id"), nullable=False)
```

**Explanation**:
- User IDs are UUIDs stored as String, not Integer
- Foreign key column must match the referenced column type

## Database Schema Relationships

### Corrected Relationships

#### Weather Data ↔ Completed Runs
```python
# WeatherData model
run_id = Column(String, ForeignKey("completed_runs.id"), nullable=True)
run = relationship("CompletedRun", back_populates="weather_data")

# CompletedRun model  
weather_data = relationship("WeatherData", back_populates="run", uselist=False)
```

#### Training Plans ↔ Users
```python
# UserTrainingPlan model
user_id = Column(String, ForeignKey("users.id"), nullable=False)
user = relationship("User", back_populates="training_plans")

# User model
training_plans = relationship("UserTrainingPlan", back_populates="user")
```

#### Weather Alerts ↔ Users
```python
# WeatherAlert model
user_id = Column(String, ForeignKey("users.id"), nullable=False)
user = relationship("User", back_populates="weather_alerts")

# User model
weather_alerts = relationship("WeatherAlert", back_populates="user")
```

## Table Structure Summary

### Core Tables
- **users**: String UUID primary key
- **completed_runs**: String UUID primary key
- **training_plans**: Integer primary key
- **weather_data**: Integer primary key
- **weather_alerts**: Integer primary key

### Foreign Key Mappings
- `weather_data.run_id` → `completed_runs.id` (String)
- `user_training_plans.user_id` → `users.id` (String)
- `weather_alerts.user_id` → `users.id` (String)
- `training_workouts.training_plan_id` → `training_plans.id` (Integer)
- `user_training_plans.training_plan_id` → `training_plans.id` (Integer)

## Verification Steps
1. ✅ All foreign key references use correct table names
2. ✅ All foreign key data types match referenced columns
3. ✅ All relationship mappings are bidirectional and consistent
4. ✅ No diagnostic errors in any model files

## Files Modified
- `backend/app/models/weather.py`
- `backend/app/models/training_plan.py`

## Database Migration Notes
If you have an existing database, you may need to:
1. Drop and recreate tables with foreign key issues
2. Or run appropriate ALTER TABLE statements to fix column types
3. The SQLAlchemy `Base.metadata.create_all()` will handle new installations

The database schema is now consistent and the backend should start without foreign key errors!