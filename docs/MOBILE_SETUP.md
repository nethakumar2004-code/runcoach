# 📱 RunCoach Mobile Setup Guide

## 🌐 Running on Mobile Data / Different Networks

### Quick Start (Using ngrok)

1. **Start the backend with ngrok:**
   ```bash
   # Double-click the start-backend-ngrok.bat file
   # OR run manually:
   
   # Terminal 1: Start backend
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 2: Start ngrok
   ngrok http 8000
   ```

2. **Copy the ngrok URL:**
   - Look for the HTTPS URL in ngrok (e.g., `https://abc123.ngrok-free.app`)
   - Copy this URL

3. **Update the mobile app:**
   - Open `mobile/runcoach-mobile/config/api.ts`
   - Replace the `NGROK` value with your new URL:
   ```typescript
   NGROK: "https://your-new-ngrok-url.ngrok-free.app",
   ```

4. **Test the connection:**
   - The app will show connection status on the login screen
   - Green = Connected ✅
   - Red = Disconnected ❌

### 🔧 Troubleshooting

#### Network Request Failed
- ✅ Check if backend server is running
- ✅ Verify ngrok tunnel is active
- ✅ Update API URL in `config/api.ts`
- ✅ Try restarting the Expo app

#### ngrok Issues
- ✅ Make sure ngrok is installed: `ngrok --version`
- ✅ Try a different port: `ngrok http 8001`
- ✅ Check ngrok dashboard: https://dashboard.ngrok.com/

#### Mobile Data Issues
- ✅ Ensure mobile data is enabled
- ✅ Try switching between WiFi and mobile data
- ✅ Check if your carrier blocks certain ports

### 🏠 Local Network (Same WiFi)

If you're on the same WiFi network:

1. **Update API config:**
   ```typescript
   // In config/api.ts, change getApiUrl() to:
   return API_CONFIG.LOCAL;
   ```

2. **Find your computer's IP:**
   ```bash
   ipconfig  # Windows
   ifconfig  # Mac/Linux
   ```

3. **Update LOCAL URL:**
   ```typescript
   LOCAL: "http://YOUR_COMPUTER_IP:8000",
   ```

### 📱 Testing on Physical Device

1. **Install Expo Go** on your phone
2. **Scan QR code** from Expo CLI
3. **Check connection status** on login screen
4. **Test signup/login** functionality

### 🚀 Production Deployment

For production, consider:
- Deploy backend to cloud (Heroku, Railway, etc.)
- Update `PRODUCTION` URL in config
- Use environment variables for different builds

### 🆘 Common Issues

| Issue | Solution |
|-------|----------|
| "Network request failed" | Check ngrok URL and backend status |
| "Server Disconnected" | Restart backend and ngrok |
| "Timeout" | Check internet connection |
| "404 Not Found" | Verify API endpoints are correct |

### 📞 Support

If you're still having issues:
1. Check the connection status indicator
2. Try the retry button
3. Restart both backend and ngrok
4. Update the ngrok URL in config/api.ts