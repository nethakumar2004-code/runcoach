@echo off
echo Populating training plans database...
cd backend
python populate_training_plans.py
echo.
echo Training plans populated! You can now see them in the app.
pause