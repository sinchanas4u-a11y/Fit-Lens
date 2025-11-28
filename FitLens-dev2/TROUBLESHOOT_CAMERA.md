# Camera Troubleshooting Guide

## 🔍 Diagnosing the Issue

### Step 1: Test Camera Directly

```bash
cd backend
python test_camera.py
```

**Expected Output:**
```
Testing camera...
✓ Camera opened successfully
✓ Frame captured: (720, 1280, 3)
Camera is working!
```

**If Failed:**
- Camera is being used by another application
- Camera permissions not granted
- No camera connected

### Step 2: Check Backend Server

```bash
cd backend
python app.py
```

**Expected Output:**
```
* Running on http://127.0.0.1:5000
```

**Check Health:**
```
http://localhost:5000/api/health
```

Should return:
```json
{
  "status": "healthy",
  "models_loaded": {
    "segmentation": false,
    "landmarks": true,
    "temporal": true
  }
}
```

### Step 3: Check Frontend Connection

Open browser console (F12) and look for:
```
Connecting to WebSocket...
WebSocket connected
Connected to server
Starting camera...
Camera started: {success: true}
```

## 🐛 Common Issues & Fixes

### Issue 1: "Starting camera..." Never Changes

**Cause:** Backend not running or not accessible

**Fix:**
```bash
# Terminal 1: Start backend
cd backend
venv\Scripts\activate
python app.py

# Terminal 2: Start frontend
cd frontend
npm start
```

**Verify:**
- Backend: http://localhost:5000/api/health
- Frontend: http://localhost:3000

### Issue 2: Camera Permission Denied

**Cause:** Browser doesn't have camera permission

**Fix:**
1. Click camera icon in address bar
2. Allow camera access
3. Refresh page

**Chrome:**
- Settings → Privacy and security → Site Settings → Camera
- Allow http://localhost:3000

### Issue 3: Camera Already in Use

**Cause:** Another application is using the camera

**Fix:**
1. Close other apps (Zoom, Teams, Skype, etc.)
2. Restart backend
3. Refresh frontend

**Check:**
```bash
# Windows: Check what's using camera
tasklist | findstr /i "camera"
```

### Issue 4: WebSocket Not Connecting

**Cause:** CORS or port issues

**Fix:**

**Backend (app.py):**
```python
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
```

**Frontend (package.json):**
```json
"proxy": "http://localhost:5000"
```

**Verify:**
- Check browser console for WebSocket errors
- Ensure backend is on port 5000
- Ensure frontend is on port 3000

### Issue 5: Blank Screen After "Starting camera..."

**Cause:** Frames not being received

**Fix:**

1. **Check Backend Logs:**
```bash
cd backend
python app.py
```

Look for:
```
Starting camera...
Camera opened successfully
Starting camera thread...
Camera thread started
Camera thread running...
```

2. **Check Frontend Console:**
```
Received camera frame
```

3. **Test Camera Endpoint:**
```bash
curl -X POST http://localhost:5000/api/camera/start
```

Should return:
```json
{"success": true}
```

### Issue 6: ModuleNotFoundError

**Cause:** Missing dependencies

**Fix:**
```bash
cd backend
pip install -r requirements.txt
```

**Required modules:**
- flask
- flask-cors
- flask-socketio
- opencv-python
- mediapipe
- numpy
- pillow

### Issue 7: Port Already in Use

**Cause:** Port 5000 or 3000 already in use

**Fix:**

**Backend:**
```python
# In app.py, change port
socketio.run(app, host='0.0.0.0', port=5001, debug=True)
```

**Frontend:**
```json
// In package.json
"proxy": "http://localhost:5001"
```

## 🔧 Debug Mode

### Enable Verbose Logging

**Backend (app.py):**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend (LiveMode.js):**
```javascript
// Add console.log statements
console.log('Current state:', { cameraActive, referenceCaptured, currentFrame });
```

### Check Network Tab

1. Open browser DevTools (F12)
2. Go to Network tab
3. Filter: WS (WebSocket)
4. Look for connection to localhost:5000

**Should see:**
- Status: 101 Switching Protocols
- Type: websocket
- Messages flowing

## 📊 Diagnostic Checklist

Run through this checklist:

- [ ] Backend server running on port 5000
- [ ] Frontend server running on port 3000
- [ ] Camera not used by other apps
- [ ] Browser has camera permission
- [ ] WebSocket connected (check console)
- [ ] No errors in backend terminal
- [ ] No errors in browser console
- [ ] Health endpoint returns healthy
- [ ] Camera test script works

## 🚀 Quick Fix Script

Create `DIAGNOSE.bat`:

```batch
@echo off
echo ============================================================
echo Camera Diagnostics
echo ============================================================
echo.

echo 1. Testing camera...
cd backend
python test_camera.py
echo.

echo 2. Checking backend health...
curl http://localhost:5000/api/health
echo.

echo 3. Testing camera start...
curl -X POST http://localhost:5000/api/camera/start
echo.

echo ============================================================
echo Diagnostics Complete
echo ============================================================
pause
```

## 📝 Manual Testing Steps

### Test 1: Camera Hardware
```python
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print(f"Camera working: {ret}")
cap.release()
```

### Test 2: Backend API
```bash
# Start backend
cd backend
python app.py

# In another terminal
curl http://localhost:5000/api/health
curl -X POST http://localhost:5000/api/camera/start
```

### Test 3: WebSocket
```javascript
// In browser console
const socket = io('http://localhost:5000');
socket.on('connect', () => console.log('Connected'));
socket.on('camera_frame', (data) => console.log('Frame received'));
```

## 🆘 Still Not Working?

### Collect Debug Info

1. **Backend logs:**
```bash
cd backend
python app.py > backend.log 2>&1
```

2. **Browser console:**
- Right-click → Inspect → Console
- Copy all errors

3. **System info:**
```bash
python --version
node --version
pip list | grep -E "flask|opencv|mediapipe"
```

### Alternative: Use MediaPipe Version

If camera still doesn't work with full-stack:

```bash
# Use standalone MediaPipe version
python pose_capture.py
```

This version has simpler camera handling and might work better.

## ✅ Success Indicators

When everything works, you should see:

**Backend Terminal:**
```
Starting camera...
Camera opened successfully
Starting camera thread...
Camera thread started
Camera thread running...
```

**Browser Console:**
```
Connecting to WebSocket...
WebSocket connected
Connected to server
Starting camera...
Camera started: {success: true}
Received camera frame
Received camera frame
...
```

**Browser UI:**
- Camera feed showing live video
- Status indicator showing "Not Ready"
- No error messages

---

**Need more help? Check:**
- Backend logs for errors
- Browser console for errors
- Camera permissions in browser
- Other apps using camera
