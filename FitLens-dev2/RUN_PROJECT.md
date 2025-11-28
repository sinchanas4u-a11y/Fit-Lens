# 🚀 How to Run the Project - Complete Guide

## Overview

You have **3 ways** to run this body measurement system:

1. **Standalone Mode** - Process images directly (fastest, easiest)
2. **Backend + Frontend Mode** - Full web application
3. **Dashboard Mode** - Simple web interface

---

## ✅ Prerequisites (Do This First!)

### Step 1: Install Dependencies

```bash
# Activate virtual environment (if you have one)
venv311\Scripts\activate

# Install YOLOv8 and core dependencies
pip install ultralytics opencv-python mediapipe numpy pillow

# OR install everything from requirements
pip install -r requirements.txt
```

### Step 2: Verify Installation

```bash
python test_yolo_setup.py
```

You should see:
```
✓ OpenCV: 4.x.x
✓ NumPy: 1.x.x
✓ MediaPipe: 0.x.x
✓ Ultralytics (YOLOv8): 8.x.x
✓ All tests passed!
```

---

## 🎯 Option 1: Standalone Mode (Recommended for Testing)

**Best for:** Quick testing, processing images, no web interface needed

### Step 1: Prepare Your Images

Place your images in the project folder or note their paths:
- `front.jpg` - Front view of person
- `side.jpg` - Side view (optional)
- `back.jpg` - Back view (optional)

### Step 2: Run the Processor

**Single Image:**
```bash
python process_images_yolo.py front.jpg
```

**Multiple Images:**
```bash
python process_images_yolo.py front.jpg side.jpg back.jpg
```

**With Height Calibration:**
```bash
python process_images_yolo.py front.jpg --reference-size 170
```
(Replace 170 with your height in cm)

**Display Results:**
```bash
python process_images_yolo.py front.jpg --display
```

**Windows Shortcut:**
```bash
RUN_YOLO_PROCESSOR.bat front.jpg side.jpg back.jpg
```

### Step 3: View Results

Check the `output/` folder for:
- `*_mask.png` - Segmentation mask
- `*_masked.png` - Clean human outline
- `*_landmarks.png` - Body keypoints
- `*_comparison.png` - Side-by-side view
- `*_measurements.png` - Annotated measurements

**Done!** You'll see measurements printed in the console and saved as images.

---

## 🌐 Option 2: Full Web Application (Backend + Frontend)

**Best for:** Complete web interface, upload mode, live camera mode

### Step 1: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

This installs:
- Flask (web server)
- Flask-CORS (cross-origin requests)
- Flask-SocketIO (real-time communication)
- All YOLOv8 dependencies

### Step 2: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

This installs React and all frontend dependencies.

### Step 3: Start Backend Server

**Option A: Command Line**
```bash
cd backend
python app.py
```

**Option B: Windows Batch File**
```bash
# From project root
cd backend
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
 * Running on http://127.0.0.1:5000
```

**Keep this terminal open!**

### Step 4: Start Frontend (New Terminal)

Open a **new terminal** and run:

```bash
cd frontend
npm start
```

You should see:
```
Compiled successfully!
Local:            http://localhost:3000
```

**Keep this terminal open too!**

### Step 5: Use the Application

1. Open browser to `http://localhost:3000`
2. You'll see two modes:
   - **Upload Mode** - Upload 3 images (front, side, reference)
   - **Live Mode** - Use webcam for real-time measurements

#### Upload Mode:
1. Click "Upload Mode"
2. Upload front view image
3. Upload side view image (optional)
4. Upload reference image (with known object)
5. Enter reference size in cm
6. Click "Process"
7. View measurements and visualizations

#### Live Camera Mode:
1. Click "Live Mode"
2. Allow camera access
3. Hold reference object (e.g., credit card)
4. Enter reference size
5. Click "Capture Reference"
6. Stand in frame, follow alignment guide
7. System auto-captures when aligned
8. View measurements

### Step 6: Stop the Application

Press `Ctrl+C` in both terminals (backend and frontend)

---

## 📊 Option 3: Dashboard Mode (Simple Web Interface)

**Best for:** Simple web interface without full React frontend

### Step 1: Run Dashboard

```bash
python dashboard_app.py
```

Or use the batch file:
```bash
RUN_DASHBOARD.bat
```

### Step 2: Open Browser

Navigate to: `http://localhost:5000`

### Step 3: Use Dashboard

1. Upload images
2. Enter reference size
3. Click "Process"
4. View results

### Step 4: Stop Dashboard

Press `Ctrl+C` in the terminal

---

## 🎮 Quick Start Commands

### For Testing (Fastest)
```bash
# Install
pip install ultralytics

# Test
python test_yolo_setup.py

# Process
python process_images_yolo.py your_image.jpg --display
```

### For Full Application
```bash
# Terminal 1: Backend
cd backend
python app.py

# Terminal 2: Frontend (new terminal)
cd frontend
npm start

# Browser: http://localhost:3000
```

### For Dashboard
```bash
python dashboard_app.py
# Browser: http://localhost:5000
```

---

## 📁 Project Structure

```
project/
├── process_images_yolo.py      # Standalone processor ⭐
├── test_yolo_setup.py          # Setup verification
├── backend/
│   ├── app.py                  # Flask backend server
│   └── requirements.txt        # Backend dependencies
├── frontend/
│   ├── src/                    # React frontend
│   └── package.json            # Frontend dependencies
├── dashboard_app.py            # Simple dashboard
├── segmentation_model.py       # YOLOv8 segmentation
├── landmark_detector.py        # MediaPipe landmarks
├── measurement_engine.py       # Measurement calculations
└── output/                     # Results folder (auto-created)
```

---

## 🔧 Troubleshooting

### "ultralytics not installed"
```bash
pip install ultralytics
```

### "No module named 'flask'"
```bash
cd backend
pip install -r requirements.txt
```

### "npm: command not found"
Install Node.js from: https://nodejs.org/

### Backend won't start
```bash
# Check if port 5000 is in use
netstat -ano | findstr :5000

# Kill process if needed
taskkill /PID <PID> /F

# Or use different port
# Edit backend/app.py, change port=5000 to port=5001
```

### Frontend won't start
```bash
# Clear cache and reinstall
cd frontend
rmdir /s /q node_modules
del package-lock.json
npm install
npm start
```

### Camera not working
- Check browser permissions
- Ensure no other app is using camera
- Try different browser (Chrome recommended)

### "No person detected"
- Ensure person is clearly visible
- Check image quality
- Good lighting
- Full body in frame

---

## 📊 Performance Tips

### For Faster Processing
```bash
# Use nano model (fastest)
python process_images_yolo.py image.jpg --model-size n

# Use GPU if available (automatic)
# YOLOv8 will use CUDA GPU if detected
```

### For Better Accuracy
```bash
# Use medium or large model
python process_images_yolo.py image.jpg --model-size m
```

### For Multiple Images
```bash
# Process batch
python process_images_yolo.py img1.jpg img2.jpg img3.jpg
```

---

## 📝 Common Workflows

### Workflow 1: Quick Test
```bash
1. pip install ultralytics
2. python test_yolo_setup.py
3. python process_images_yolo.py test.jpg --display
4. Check output/ folder
```

### Workflow 2: Process Multiple People
```bash
1. Prepare images: person1.jpg, person2.jpg, person3.jpg
2. python process_images_yolo.py person1.jpg
3. python process_images_yolo.py person2.jpg
4. python process_images_yolo.py person3.jpg
5. Compare results in output/ folder
```

### Workflow 3: Full Web Application
```bash
1. cd backend && python app.py
2. (New terminal) cd frontend && npm start
3. Open http://localhost:3000
4. Use upload or live mode
5. Export results
```

### Workflow 4: Batch Processing
```bash
1. Create folder: mkdir images
2. Copy all images to images/
3. Run: python example_usage.py
4. Uncomment example_6_batch_processing()
5. Check output/ folder
```

---

## 🎯 Recommended Approach

### For First Time Users:
1. **Start with Standalone Mode**
   ```bash
   python process_images_yolo.py your_image.jpg --display
   ```

2. **If it works, try multiple images**
   ```bash
   python process_images_yolo.py front.jpg side.jpg back.jpg
   ```

3. **Then try the web application**
   ```bash
   # Terminal 1
   cd backend && python app.py
   
   # Terminal 2
   cd frontend && npm start
   ```

### For Production Use:
1. Use the full web application (Backend + Frontend)
2. Deploy backend to cloud server
3. Deploy frontend to hosting service
4. Configure CORS and security

---

## 📞 Need Help?

### Quick Issues
- Check `START_HERE_YOLO.md`
- Check `QUICKSTART_YOLO.md`

### Detailed Help
- Check `YOLO_GUIDE.md`
- Check `README_YOLO.md`

### Code Examples
- Check `example_usage.py`

### System Flow
- Check `SYSTEM_FLOW.md`

---

## ✅ Success Checklist

Before running:
- [ ] Python 3.8+ installed
- [ ] Dependencies installed (`pip install ultralytics`)
- [ ] Setup test passed (`python test_yolo_setup.py`)
- [ ] Images prepared (good quality, full body visible)

For standalone mode:
- [ ] Run `python process_images_yolo.py image.jpg`
- [ ] Check `output/` folder
- [ ] Measurements displayed

For web application:
- [ ] Backend running (`cd backend && python app.py`)
- [ ] Frontend running (`cd frontend && npm start`)
- [ ] Browser open to `http://localhost:3000`
- [ ] Can upload images or use camera

---

## 🎉 You're Ready!

Choose your mode and start:

**Quick Test:**
```bash
python process_images_yolo.py your_image.jpg --display
```

**Full Application:**
```bash
# Terminal 1: cd backend && python app.py
# Terminal 2: cd frontend && npm start
# Browser: http://localhost:3000
```

**Simple Dashboard:**
```bash
python dashboard_app.py
# Browser: http://localhost:5000
```

---

## 📋 Quick Reference Card

| Task | Command |
|------|---------|
| Install | `pip install ultralytics` |
| Test Setup | `python test_yolo_setup.py` |
| Process Image | `python process_images_yolo.py image.jpg` |
| Multiple Images | `python process_images_yolo.py img1.jpg img2.jpg` |
| With Calibration | `python process_images_yolo.py img.jpg --reference-size 170` |
| Display Results | `python process_images_yolo.py img.jpg --display` |
| Start Backend | `cd backend && python app.py` |
| Start Frontend | `cd frontend && npm start` |
| Start Dashboard | `python dashboard_app.py` |

---

**Questions?** Read `START_HERE_YOLO.md` or `YOLO_GUIDE.md`

**Ready?** Pick a mode and go! 🚀
