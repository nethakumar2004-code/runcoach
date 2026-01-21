# Fix iOS Location Permissions

## The Issue
The error `NSLocation*UsageDescription keys must be present in Info.plist` occurs because the iOS native project needs to be regenerated with the new location permissions.

## Solution Steps

### 1. Stop the Current Development Server
```bash
# Press Ctrl+C to stop the current expo start process
```

### 2. Clear Expo Cache and Regenerate Native Code
```bash
cd mobile/runcoach-mobile

# Clear all caches
npx expo start --clear --reset-cache

# If that doesn't work, try:
rm -rf node_modules/.cache
rm -rf .expo
npx expo start --clear
```

### 3. Alternative: Prebuild (if using development build)
```bash
# If you're using a development build, regenerate native code:
npx expo prebuild --clean
```

### 4. For iOS Simulator/Device Testing
If you're testing on iOS and the permissions still don't work:

```bash
# Install iOS dependencies
npx expo install --ios

# Start with iOS focus
npx expo start --ios
```

## Why This Happens

1. **Expo Go**: The location permissions in app.json should work automatically
2. **Development Build**: Requires prebuild to regenerate native iOS project
3. **Cache Issues**: Sometimes Expo cache needs clearing to pick up app.json changes

## Verification

After restarting, you should see:
- ✅ No more Info.plist errors
- ✅ Location permission dialog appears on iOS
- ✅ GPS tracking works properly

## Current app.json Configuration ✅

Your app.json already has the correct configuration:

```json
{
  "ios": {
    "infoPlist": {
      "NSLocationAlwaysAndWhenInUseUsageDescription": "This app needs access to location for GPS tracking during runs.",
      "NSLocationWhenInUseUsageDescription": "This app needs access to location for GPS tracking during runs.",
      "NSLocationAlwaysUsageDescription": "This app needs access to location for GPS tracking during runs."
    }
  },
  "plugins": [
    [
      "expo-location",
      {
        "locationAlwaysAndWhenInUsePermission": "This app needs access to location for GPS tracking during runs.",
        "locationAlwaysPermission": "This app needs access to location for GPS tracking during runs.",
        "locationWhenInUsePermission": "This app needs access to location for GPS tracking during runs."
      }
    ]
  ]
}
```

## Quick Fix Command

```bash
cd mobile/runcoach-mobile
npx expo start --clear --reset-cache
```

This should resolve the iOS location permission issue! 🎉