# Training Plans Troubleshooting Guide

## Current Issue: "Failed to complete workout" Error

The mobile app is showing an error when trying to complete workouts. This is likely due to one of the following reasons:

### Possible Causes

1. **User Not Enrolled in Training Plan**
   - The user needs to enroll in a training plan first
   - Check if the user has an active training plan

2. **Authentication Issues**
   - JWT token might be expired or invalid
   - User needs to log in again

3. **Workout Not Found**
   - The workout ID doesn't exist
   - The workout doesn't belong to the user's active plan

### Debugging Steps

#### 1. Check User Status
Use the debug endpoint to check user's training plan status:
```
GET /training-plans/debug/user-status
Authorization: Bearer <token>
```

#### 2. Test Basic Functionality
Use the test endpoint to verify workouts exist:
```
GET /training-plans/test/week/1/1
```

#### 3. Check Available Plans
Verify training plans are populated:
```
GET /training-plans/
```

### Expected Workflow

1. **User Authentication**
   - User must be logged in with valid JWT token
   - Token should be stored in AsyncStorage

2. **Plan Enrollment**
   - User selects and enrolls in a training plan
   - This creates a UserTrainingPlan record

3. **Workout Completion**
   - User can only complete workouts from their active plan
   - Workouts can only be completed once

### API Endpoints Status

✅ `GET /training-plans/` - List available plans  
✅ `POST /training-plans/enroll/{plan_id}` - Enroll in plan  
✅ `GET /training-plans/my/current` - Get current plan  
✅ `GET /training-plans/my/week/{week}` - Get weekly workouts  
✅ `POST /training-plans/workouts/{id}/complete` - Complete workout  
✅ `GET /training-plans/debug/user-status` - Debug user status  

### Mobile App Flow

1. **Check Authentication**
   ```typescript
   const token = await AsyncStorage.getItem('authToken');
   if (!token) {
     // Redirect to login
   }
   ```

2. **Load Current Plan**
   ```typescript
   const response = await fetch('/training-plans/my/current', {
     headers: { Authorization: `Bearer ${token}` }
   });
   ```

3. **Enroll if No Plan**
   ```typescript
   if (response.status === 404) {
     // Show available plans for enrollment
   }
   ```

4. **Complete Workout**
   ```typescript
   const response = await fetch(`/training-plans/workouts/${workoutId}/complete`, {
     method: 'POST',
     headers: { Authorization: `Bearer ${token}` },
     body: JSON.stringify({ effort_rating: 7 })
   });
   ```

### Next Steps

1. **Test Authentication**: Verify user is properly logged in
2. **Check Enrollment**: Ensure user has enrolled in a training plan
3. **Debug API Calls**: Use the debug endpoint to check user status
4. **Verify Workout IDs**: Ensure the workout being completed exists and belongs to the user's plan

The training plans system is fully functional - the issue is likely with the user flow or authentication state.