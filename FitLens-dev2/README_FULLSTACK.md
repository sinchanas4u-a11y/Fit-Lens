# Body Measurement System - Full-Stack Application

Modern web-based body measurement system with React frontend and Flask backend.

## 🌟 Features

### Two Operating Modes

**📤 Upload Mode**
- Upload front, side, and reference images
- Batch processing
- Detailed results with confidence scores
- Visualization overlays

**📷 Live Camera Mode**
- Real-time pose detection
- Color-coded alignment feedback (Red/Amber/Green)
- Auto-capture after 3 seconds
- Manual capture option
- Voice guidance
- Live feedback log

### Advanced Technologies

- **Frontend**: React 18 + Material-UI
- **Backend**: Flask + Socket.IO
- **ML Models**: Mask R-CNN, MediaPipe, LSTM
- **Real-time**: WebSocket streaming
- **Responsive**: Works on desktop and tablet

## 🚀 Quick Start

### Automated Setup & Run

```bash
# Setup (first time only)
SETUP_FULLSTACK.bat

# Run application
RUN_FULLSTACK.bat
```

Then open: `http://localhost:3000`

### Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

## 📁 File Structure

```
Body-Measurement-System/
│
├── backend/                      # Flask API Server
│   ├── app.py                   # Main API server
│   ├── reference_detector.py   # Reference detection
│   ├── temporal_stabilizer.py  # LSTM stability
│   ├── measurement_engine.py   # Measurements
│   ├── segmentation_model.py   # Mask R-CNN
│   ├── landmark_detector.py    # MediaPipe
│   └── requirements.txt        # Python deps
│
├── frontend/                     # React Application
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.js    # Main dashboard
│   │   │   ├── UploadMode.js   # Upload interface
│   │   │   └── LiveMode.js     # Live camera
│   │   ├── App.js              # Main app
│   │   ├── App.css             # Styles
│   │   └── index.js            # Entry point
│   └── package.json            # Node deps
│
├── SETUP_FULLSTACK.bat          # Automated setup
├── RUN_FULLSTACK.bat            # Run both servers
├── SETUP_FULLSTACK.md           # Detailed setup guide
└── README_FULLSTACK.md          # This file
```

## 🎯 How to Use

### Upload Mode

1. **Launch Application**
   - Open `http://localhost:3000`
   - Click "Upload Images"

2. **Prepare Reference**
   - Enter known size (e.g., 29.7 cm for A4 paper)
   - Select axis (width or height)

3. **Upload Images**
   - Upload reference object photo
   - Upload front view (full body)
   - Upload side view (optional)

4. **Process**
   - Click "Process & Measure"
   - Wait for results (~10-30 seconds)

5. **View Results**
   - See measurements table
   - Check confidence scores
   - View visualization overlay

### Live Camera Mode

1. **Launch Application**
   - Open `http://localhost:3000`
   - Click "Live Camera"
   - Allow camera access

2. **Capture Reference**
   - Place reference object in frame
   - Enter known size
   - Click "Capture Reference"
   - Keep object visible

3. **Align Body**
   - Stand in front of camera
   - Follow color-coded feedback:
     - 🔴 Red: Adjust position
     - 🟡 Amber: Almost ready
     - 🟢 Green: Perfect!

4. **Auto-Capture**
   - When green, hold still
   - 3-second countdown
   - Auto-capture triggers
   - Or use "Manual Capture"

5. **View Results**
   - See measurements
   - Check confidence scores
   - Review feedback log

## 🎨 User Interface

### Dashboard
- Clean, modern design
- Two large mode buttons
- Feature list
- Dark theme

### Upload Mode
- Left panel: Controls
- Right panel: Preview & Results
- Drag-and-drop support
- Real-time preview

### Live Mode
- Left panel: Controls & Feedback
- Right panel: Camera feed
- Status indicator
- Countdown display
- Voice guidance toggle

## 🔧 API Documentation

### REST Endpoints

```
GET  /api/health
POST /api/upload/process
POST /api/camera/start
POST /api/camera/stop
POST /api/camera/capture-reference
POST /api/camera/capture-measurement
```

### WebSocket Events

```
camera_frame: Real-time camera frames
```

See `SETUP_FULLSTACK.md` for detailed API docs.

## 📊 Measurements Provided

### Front View
- Shoulder Width
- Hip Width
- Chest Width
- Waist Width
- Arm Span

### Side View
- Torso Depth
- Shoulder to Hip
- Hip to Ankle

### Each Measurement Includes
- Value (cm)
- Confidence Score (0-1)
- Source (MediaPipe/Estimated)

## 🎤 Voice Guidance

Enable voice guidance for hands-free operation:
- Reference capture confirmation
- Alignment status updates
- Capture notifications
- Error messages

Toggle on/off in Live Mode interface.

## 🔒 Privacy & Security

- **Local Processing**: All processing happens locally
- **No Cloud Upload**: Images never leave your machine
- **Temporary Storage**: Data cleared after session
- **User Control**: You control what gets saved

For production deployment, see security section in `SETUP_FULLSTACK.md`.

## 🐛 Troubleshooting

### Backend Won't Start

```bash
# Check Python version
python --version  # Should be 3.11

# Check dependencies
cd backend
pip list

# Reinstall
pip install -r requirements.txt
```

### Frontend Won't Start

```bash
# Check Node version
node --version  # Should be 16+

# Clear cache
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Camera Not Working

- Check browser permissions
- Ensure no other app is using camera
- Try different browser (Chrome recommended)
- Check backend logs for errors

### WebSocket Connection Failed

- Ensure backend is running on port 5000
- Check firewall settings
- Verify proxy configuration in package.json

## 📈 Performance Tips

### For Better Speed

1. **Use GPU**: Ensure CUDA is available
2. **Reduce Quality**: Lower camera resolution
3. **Lighter Models**: Use model_complexity=1
4. **Close Other Apps**: Free up resources

### For Better Accuracy

1. **Good Lighting**: Even, bright lighting
2. **Plain Background**: Solid color
3. **Proper Distance**: 2-3 meters from camera
4. **Fitted Clothing**: Shows body shape better
5. **Multiple Captures**: Average 3-5 measurements

## 🚢 Deployment

### Development
```bash
# Backend: http://localhost:5000
# Frontend: http://localhost:3000
```

### Production

**Backend (Heroku):**
```bash
heroku create your-app-backend
git subtree push --prefix backend heroku main
```

**Frontend (Vercel):**
```bash
cd frontend
vercel deploy
```

See `SETUP_FULLSTACK.md` for detailed deployment guide.

## 🎓 Technology Stack

### Frontend
- React 18
- Material-UI 5
- Socket.IO Client
- Axios
- React Webcam

### Backend
- Flask 2.3
- Flask-SocketIO
- OpenCV
- MediaPipe
- PyTorch
- Detectron2 (optional)

### ML Models
- Mask R-CNN (person segmentation)
- MediaPipe Pose (33 landmarks)
- LSTM (temporal stability)

## 📚 Documentation

- `README_FULLSTACK.md` - This file (overview)
- `SETUP_FULLSTACK.md` - Detailed setup & API docs
- `DASHBOARD_GUIDE.md` - User guide for desktop app
- `ARCHITECTURE.md` - System architecture

## 🆘 Support

### Common Issues

**Q: Models not loading?**
A: Check GPU/CUDA availability, or use CPU mode.

**Q: Slow performance?**
A: Use GPU, reduce resolution, or use lighter models.

**Q: Measurements inaccurate?**
A: Verify reference size, improve lighting, take multiple captures.

**Q: Camera feed laggy?**
A: Reduce FPS in backend, close other applications.

## 🔄 Updates & Maintenance

### Update Dependencies

**Backend:**
```bash
cd backend
pip install --upgrade -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm update
```

### Check for Issues

**Backend:**
```bash
cd backend
python -m pytest tests/
```

**Frontend:**
```bash
cd frontend
npm test
```

## 🎯 Roadmap

### Planned Features
- [ ] Multi-person support
- [ ] 3D body model visualization
- [ ] Export measurements to PDF
- [ ] Measurement history tracking
- [ ] User accounts & profiles
- [ ] Mobile app (React Native)
- [ ] Cloud deployment option

## 🤝 Contributing

This is a complete, production-ready system. Feel free to:
- Add new measurements
- Improve UI/UX
- Optimize performance
- Add new features

## 📄 License

MIT License - Free to use and modify

---

## ✅ Quick Reference

### Start Application
```bash
RUN_FULLSTACK.bat
```

### Access Application
```
http://localhost:3000
```

### Stop Application
```
Press any key in RUN_FULLSTACK window
```

### Check Status
```
Backend: http://localhost:5000/api/health
Frontend: http://localhost:3000
```

---

**Ready to measure? Run:** `RUN_FULLSTACK.bat` 🚀
