# 🚀 START HERE - Quick Setup Guide

## Current Status

✅ **Backend is running!** (Port 5000)

## What You Need to Do

### Step 1: Test Backend API (Optional)

In the backend terminal, test if camera works:

```bash
python test_api.py
```

You should see:
```
✓ Camera started successfully!
Check backend terminal for 'Starting camera...' message
```

### Step 2: Start Frontend

**Open a NEW terminal** (keep backend running) and run:

```bash
cd frontend
npm start
```

**First time?** Install dependencies first:
```bash
cd frontend
npm install
npm start
```

Frontend will start on: **http://localhost:3000**

### Step 3: Open Browser

1. Open: **http://localhost:3000**
2. Click **"Live Camera"** button
3. Allow camera permissions if asked

### Step 4: Watch Backend Terminal

When you click "Live Camera", you should see:
```
Starting camera...
Camera opened successfully
Starting camera thread...
Camera thread started
Camera thread running...
```

### Step 5: Check Browser

- Camera feed should appear
- Status should show "Not Ready"
- No blank screen

## 🎯 Quick Commands

### Terminal 1 (Backend):
```bash
cd backend
venv\Scripts\activate
python app.py
```

### Terminal 2 (Frontend):
```bash
cd frontend
npm start
```

### Browser:
```
http://localhost:3000
```

## 🐛 If Frontend Won't Start

### Error: "npm: command not found"
**Solution:** Install Node.js from https://nodejs.org/

### Error: "Cannot find module"
**Solution:**
```bash
cd frontend
npm install
npm start
```

### Error: "Port 3000 already in use"
**Solution:**
```bash
# Kill the process using port 3000
# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Then start again
npm start
```

## ✅ Success Checklist

- [ ] Backend running (you have this ✓)
- [ ] Frontend running (do this next)
- [ ] Browser open at localhost:3000
- [ ] Clicked "Live Camera"
- [ ] Camera feed visible

## 📝 What Happens When You Click "Live Camera"

1. Frontend sends POST to `/api/camera/start`
2. Backend prints "Starting camera..."
3. Backend opens camera (cv2.VideoCapture)
4. Backend starts streaming thread
5. Frontend receives frames via WebSocket
6. Camera feed displays in browser

## 🎥 Why You Don't See "Starting camera..." Yet

The backend is **waiting** for the frontend to call the API.

**The message will appear when:**
- Frontend is running
- You open http://localhost:3000
- You click "Live Camera" button

## 🚀 Next Step

**Start the frontend now:**

```bash
# Open NEW terminal
cd frontend
npm start
```

Then open http://localhost:3000 in your browser!

---

**Need help?** See:
- `TEST_CONNECTION.md` - Connection testing
- `TROUBLESHOOT_CAMERA.md` - Detailed troubleshooting
- `DIAGNOSE.bat` - Automated diagnostics
