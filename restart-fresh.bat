@echo off
echo 🚀 Restarting RunCoach with fresh cache...
echo.

echo Step 1: Clearing all caches...
cd mobile\runcoach-mobile
node force-refresh.js

echo.
echo Step 2: Testing API configuration...
node test-config.js

echo.
echo Step 3: Starting Expo with fresh cache...
echo ⚠️  IMPORTANT: Make sure to scan the QR code again!
echo.
npx expo start --clear --tunnel

pause