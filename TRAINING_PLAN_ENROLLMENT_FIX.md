# Training Plan Enrollment Error Fix

## Issue Identified
The training plan enrollment error occurs because users need to authenticate before enrolling in training plans. The app supports a development token system for testing.

## Root Cause
- Users attempting to enroll without setting up authentication
- The error "Failed to enroll in plan" is thrown when no auth token is present
- The backend requires authentication for the `/training-plans/enroll/{plan_id}` endpoint

## Solution Implemented

### 1. Enhanced Error Handling
- Added detailed logging to track enrollment process
- Better error messages for authentication issues
- Specific handling for 401 (unauthorized) responses

### 2. Authentication Guidance
- Clear instructions when no token is present
- Guidance to use the Debug screen for setting dev token
- Automatic token cleanup on authentication errors

### 3. Development Token Support
- Backend supports `dev-token` for development/testing
- Creates test user automatically when using dev token
- No need for complex authentication setup during development

## How to Fix the Issue

### For Users:
1. **Navigate to Debug Screen** (if available in app navigation)
2. **Set Development Token**:
   - Tap "🔧 Set Dev Token" button
   - This sets the auth token to "dev-token"
   - Backend will automatically create a test user

3. **Try Enrollment Again**:
   - Go back to Training Plans
   - Select a plan to enroll
   - Should work with proper authentication

### For Developers:
1. **Manual Token Setting** (if debug screen not accessible):
   ```javascript
   // In React Native console or temporary code
   import AsyncStorage from '@react-native-async-storage/async-storage';
   AsyncStorage.setItem('authToken', 'dev-token');
   ```

2. **Verify Token**:
   ```javascript
   AsyncStorage.getItem('authToken').then(token => console.log('Token:', token));
   ```

## Backend Authentication Flow

### Development Mode:
- Token: `dev-token`
- Creates test user: `test@example.com`
- Password: `password123` (hashed)
- Experience level: `intermediate`

### Production Mode:
- Requires proper JWT tokens
- Users must register/login through auth endpoints
- Tokens expire after 30 days

## Files Modified

### Frontend:
- `mobile/runcoach-mobile/components/TrainingPlan.tsx`
  - Enhanced error handling
  - Better authentication guidance
  - Detailed logging for debugging

### Backend:
- `backend/app/routers/training_plans.py`
  - Added test enrollment endpoint
  - Enhanced error logging

### Existing Support:
- `backend/app/dependencies.py` - Already supports dev-token
- `mobile/runcoach-mobile/app/debug.tsx` - Already has token management

## Testing the Fix

1. **Clear existing token** (if any):
   ```javascript
   AsyncStorage.removeItem('authToken');
   ```

2. **Set development token**:
   ```javascript
   AsyncStorage.setItem('authToken', 'dev-token');
   ```

3. **Test enrollment**:
   - Open Training Plans
   - Select any plan (5K, 10K, or Half Marathon)
   - Should successfully enroll

4. **Verify enrollment**:
   - Should see plan details and weekly workouts
   - Can navigate between weeks
   - Can mark workouts as complete

## Error Prevention

### User-Friendly Messages:
- "Authentication Required" instead of generic errors
- Clear instructions on how to fix the issue
- Option to navigate to debug/auth screen

### Developer Debugging:
- Console logs for all API calls
- Response status and error details
- Token presence verification

## Next Steps

1. **Add Navigation**: Ensure users can easily access the Debug screen
2. **Onboarding**: Add initial setup flow for new users
3. **Production Auth**: Implement proper login/register flow
4. **Error Recovery**: Auto-retry with token refresh

The training plan enrollment should now work properly once users set up authentication using the development token system.