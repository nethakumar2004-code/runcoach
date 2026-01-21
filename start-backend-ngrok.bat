@echo off
echo Starting RunCoach Backend with ngrok...
echo.

echo Step 1: Starting FastAPI server...
start "FastAPI Server" cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo Waiting for server to start...
timeout /t 5 /nobreak > nul

echo Step 2: Starting ngrok tunnel...
start "ngrok" cmd /k "ngrok http 8000"

echo.
echo ========================================
echo IMPORTANT: 
echo 1. Wait for ngrok to show the HTTPS URL
echo 2. Copy the ngrok HTTPS URL (like https://abc123.ngrok-free.app)
echo 3. Update mobile/runcoach-mobile/config/api.ts with your ngrok URL
echo 4. Replace the NGROK value with your new URL
echo ========================================
echo.
pause