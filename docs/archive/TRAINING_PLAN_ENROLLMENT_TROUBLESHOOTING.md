# Training Plan Enrollment Troubleshooting Guide

## Current Issue
Users are still experiencing 404 "Not Found" errors when trying to enroll in training plans, despite the backend endpoint working correctly.

## Quick Fix for Users

### Option 1: Use the Training Plan Screen
1. **Navigate to Training Plans**
2. **Look for the yellow debug section** at the top
3. **Tap "🔑 Set Dev Token"** - this will set up authentication
4. **Try enrolling in a plan again**

### Option 2: Use the Debug Screen
1. **Navigate to Debug screen** (if available in app navigation)
2. **Tap "🔧 Set Dev Token"**
3. **Return to Training Plans and try enrollment**

### Option 3: Manual Token Setting (Advanced)
If you have access to React Native debugger:
```javascript
import AsyncStorage from '@react-native-async-storage/async-storage';
AsyncStorage.setItem('authToken', 'dev-token');
```

## Verification Steps

### 1. Test Authentication
- Use the "🔧 Test Authentication" button on Training Plans screen
- Should show success with user ID if working properly

### 2. Check API Connection
- The app should be using ngrok URL: `https://unextinguishable-britteny-unpulsating.ngrok-free.dev`
- Backend is confirmed working through this URL

### 3. Verify Enrollment
- After setting dev token, enrollment should work
- Should see success message and access to weekly workouts

## Technical Details

### Backend Status: ✅ WORKING
- Enrollment endpoint: `POST /training-plans/enroll/{plan_id}` ✅
- Authentication with dev-token: ✅
- Database operations: ✅
- ngrok accessibility: ✅

### Frontend Status: ⚠️ NEEDS TOKEN SETUP
- API configuration: ✅ (using ngrok)
- Enrollment function: ✅ (enhanced with debugging)
- Authentication: ❌ (users need to set dev token)

## Root Cause Analysis

The 404 error is likely caused by one of these issues:

1. **No Authentication Token**: User hasn't set the dev token
2. **Invalid Token**: Token exists but is not 'dev-token'
3. **Network Issues**: Mobile app can't reach ngrok URL
4. **Caching Issues**: Old API responses being cached

## Enhanced Debugging

The TrainingPlan component now includes:
- **Enhanced logging**: Shows API URL, token status, and full request details
- **Quick fix button**: "🔑 Set Dev Token" for immediate token setup
- **Authentication test**: Verify connection before enrollment
- **Better error messages**: Clear guidance for users

## Expected Log Output (Success)
```
Enrolling in plan 1 with token: present
API_BASE: https://unextinguishable-britteny-unpulsating.ngrok-free.dev
Full URL: https://unextinguishable-britteny-unpulsating.ngrok-free.dev/training-plans/enroll/1
Enrollment response status: 200
Enrollment successful: {success: true, user_plan_id: 23, ...}
```

## Expected Log Output (Failure)
```
Enrolling in plan 1 with token: missing
// OR
Enrolling in plan 1 with token: present
API_BASE: https://unextinguishable-britteny-unpulsating.ngrok-free.dev
Full URL: https://unextinguishable-britteny-unpulsating.ngrok-free.dev/training-plans/enroll/1
Enrollment response status: 404
Enrollment failed: 404 {"detail":"Not Found"}
```

## Next Steps for Users

1. **Try the quick fix**: Use "🔑 Set Dev Token" button
2. **Test authentication**: Use "🔧 Test Authentication" button
3. **Check logs**: Look for the enhanced debug output
4. **Report results**: Share the log output if issues persist

## For Developers

### Verify Backend
```bash
# Test enrollment endpoint directly
curl -X POST "https://unextinguishable-britteny-unpulsating.ngrok-free.dev/training-plans/enroll/1" \
     -H "Authorization: Bearer dev-token" \
     -H "ngrok-skip-browser-warning: true"
```

### Check Mobile App State
```javascript
// Check current token
AsyncStorage.getItem('authToken').then(token => console.log('Current token:', token));

// Test API connection
fetch('https://unextinguishable-britteny-unpulsating.ngrok-free.dev/training-plans/')
  .then(r => r.json())
  .then(data => console.log('API working:', data.length, 'plans'));
```

The enrollment system is working correctly on the backend. The issue is primarily a frontend authentication setup problem that can be resolved by setting the development token.