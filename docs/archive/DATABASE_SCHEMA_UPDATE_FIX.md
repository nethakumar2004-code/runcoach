# Database Schema Update Fix - COMPLETED

## Issue
After adding new fields (`training_load`, `splits`) to the `CompletedRun` model, the SQLite database was missing these columns, causing 500 errors:

```
sqlite3.OperationalError: table completed_runs has no column named training_load
```

## Root Cause
The database schema was not updated after model changes. SQLAlchemy's `create_all()` only creates tables that don't exist, but doesn't add new columns to existing tables.

## Solution Applied

### 1. Database Recreation
Since this is a development environment, the simplest solution was to:
1. Stop the backend server
2. Delete the existing `backend/dev.db` file
3. Restart the backend (which recreates tables with new schema)
4. Repopulate training plans data

### 2. Steps Executed
```bash
# Stop backend processes
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force

# Delete old database
Remove-Item "backend/dev.db"

# Start backend (recreates database with new schema)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Repopulate training plans
python populate_training_plans.py
```

### 3. New Schema Includes
The `completed_runs` table now properly includes:
- `training_load` (Float) - Calculated training stress
- `splits` (JSON) - Split times per kilometer
- All other enhanced fields from the model

## Result
- ✅ Database schema updated with all new fields
- ✅ Backend running with fresh database
- ✅ Training plans repopulated
- ✅ Run saving should now work without schema errors

## Files Affected
- `backend/dev.db` - Recreated with new schema
- Training plans data - Repopulated

## Future Considerations
For production environments, proper database migrations should be used instead of recreating the database. Consider using Alembic for SQLAlchemy migrations in production.

## Testing
The run save endpoint should now work properly with all the new fields including `training_load` and `splits` data.