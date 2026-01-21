# 🚨 Quick Fix for "Internet connection appears to be offline"

## 🔧 **Immediate Steps:**

### 1. **Check if backend is running:**
```bash
# In terminal 1:
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. **Check if ngrok is running:**
```bash
# In terminal 2:
ngrok http 8000
```

### 3. **Get your ngrok URL:**
- Look for the HTTPS URL in ngrok terminal (like `https://abc123.ngrok-free.app`)
- Copy this URL

### 4. **Update the mobile app:**
- Open `mobile/runcoach-mobile/config/api.ts`
- Update the NGROK URL:
```typescript
NGROK: "https://your-new-ngrok-url.ngrok-free.app",
```

### 5. **Clear Expo cache:**
```bash
cd mobile/runcoach-mobile
npx expo start --clear
```

### 6. **Use the Debug Tool:**
- In your app, tap "🔧 Debug Connection" on the login screen
- This will test your API connection and show detailed results

## 🎯 **What the Debug Tool Shows:**

- ✅ **Green**: API is working perfectly
- ❌ **Red**: Connection failed - check backend/ngrok
- 🟡 **Yellow**: Testing connection...

## 📱 **Testing Steps:**

1. **Open the app**
2. **Tap "🔧 Debug Connection"**
3. **Tap "🔄 Test Connection"**
4. **If red, check backend and ngrok**
5. **Tap "📝 Test Signup" to test the API**

## 🆘 **Still Not Working?**

### Check these:
- [ ] Backend server is running on port 8000
- [ ] ngrok tunnel is active and showing HTTPS URL
- [ ] Mobile app config has the correct ngrok URL
- [ ] You cleared Expo cache with `--clear`
- [ ] Your phone has internet connection

### Common Issues:
| Problem | Solution |
|---------|----------|
| "Network request failed" | Update ngrok URL in config |
| "Server Disconnected" | Restart backend and ngrok |
| "Connection timeout" | Check internet connection |
| App shows old IP | Clear Expo cache |

## 🎉 **Success Indicators:**
- Debug tool shows 🟢 Connected
- Test signup returns status 200
- You can create an account

Your app should work on any network once the debug tool shows green! 🚀