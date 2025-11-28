# Test Connection Between Frontend and Backend

## Current Status

✅ Backend is running on http://127.0.0.1:5000

## Next Steps

### 1. Start Frontend

Open a NEW terminal and run:

```bash
cd frontend
npm start
```

This will start the frontend on http://localhost:3000

### 2. Open Browser

Navigate to: http://localhost:3000

### 3. Click "Live Camera"

This should trigger the camera start.

### 4. Check Backend Terminal

You should now see:
```
Starting camera...
Camera opened successfully
Starting camera thread...
Camera thread started
Camera thread running...
```

### 5. Check Browser Console (F12)

You should see:
```
Connecting to WebSocket...
WebSocket connected
Connected to server
Starting camera...
Camera started: {success: true}
Received camera frame
```

## If Frontend Not Starting

### Install Dependencies First

```bash
cd frontend
npm install
```

Then:
```bash
npm start
```

## Quick Test Without Frontend

You can test the backend directly:

### Test 1: Health Check
```bash
curl http://localhost:5000/api/health
```

### Test 2: Start Camera
```bash
curl -X POST http://localhost:5000/api/camera/start
```

After this, you should see "Starting camera..." in the backend terminal.

## Current Issue

The backend is running but waiting for the frontend to call `/api/camera/start`.

**Solution:** Start the frontend with `npm start` in the frontend directory.
