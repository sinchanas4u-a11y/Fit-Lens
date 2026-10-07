# Full-Stack Body Measurement System Setup

Complete setup guide for the frontend + backend application.

## 🏗️ Architecture

```
Body Measurement System
├── Backend (Flask API)
│   ├── REST API endpoints
│   ├── WebSocket for live streaming
│   ├── ML models (Mask R-CNN, MediaPipe, LSTM)
│   └── Image processing
│
└── Frontend (React)
    ├── Dashboard
    ├── Upload Mode
    ├── Live Camera Mode
    └── Real-time visualization
```

## 📋 Prerequisites

- Python 3.11
- Node.js 16+ and npm
- Webcam (for live mode)
- 8GB+ RAM
- GPU recommended (for Mask R-CNN)

## 🚀 Quick Start

### Option 1: Automated Setup (Windows)

```bash
# Run the setup script
SETUP_FULLSTACK.bat
```

### Option 2: Manual Setup

#### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install Detectron2 for Mask R-CNN
pip install git+https://github.com/facebookresearch/detectron2.git

# Run backend
python app.py
```

Backend will run on: `http://localhost:5000`

#### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend will run on: `http://localhost:3000`

## 📁 Project Structure

```
.
├── backend/
│   ├── app.py                    # Flask API server
│   ├── reference_detector.py    # Reference object detection
│   ├── temporal_stabilizer.py   # LSTM stability checker
│   ├── measurement_engine.py    # Measurement calculations
│   ├── segmentation_model.py    # Mask R-CNN segmentation
│   ├── landmark_detector.py     # MediaPipe landmarks
│   └── requirements.txt         # Python dependencies
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.js     # Main dashboard
│   │   │   ├── UploadMode.js    # Upload interface
│   │   │   └── LiveMode.js      # Live camera interface
│   │   ├── App.js               # Main app component
│   │   ├── App.css              # Styles
│   │   ├── index.js             # Entry point
│   │   └── index.css            # Global styles
│   └── package.json             # Node dependencies
│
└── SETUP_FULLSTACK.md           # This file
```

## 🔧 Configuration

### Backend Configuration

Edit `backend/app.py` to configure:

```python
# Server settings
HOST = '0.0.0.0'
PORT = 5000
DEBUG = True

# Model settings
DETECTION_THRESHOLD = 0.5
KEYPOINT_THRESHOLD = 0.5
```

### Frontend Configuration

Edit `frontend/package.json` proxy:

```json
"proxy": "http://localhost:5000"
```

For production, update API URLs in components.

## 🎯 API Endpoints

### REST Endpoints

**Health Check**
```
GET /api/health
Response: { status, models_loaded }
```

**Process Upload**
```
POST /api/upload/process
Body: {
  front_image: base64,
  side_image: base64,
  reference_image: base64,
  reference_size: float,
  reference_axis: "width" | "height"
}
Response: { success, scale_factor, results }
```

**Start Camera**
```
POST /api/camera/start
Response: { success }
```

**Stop Camera**
```
POST /api/camera/stop
Response: { success }
```

**Capture Reference**
```
POST /api/camera/capture-reference
Body: {
  reference_size: float,
  reference_axis: "width" | "height"
}
Response: { success, reference_px, scale_factor }
```

**Capture Measurement**
```
POST /api/camera/capture-measurement
Response: { success, result }
```

### WebSocket Events

**camera_frame**
```
Event: camera_frame
Data: { frame: base64, timestamp: float }
```

## 🎨 Frontend Features

### Dashboard
- Mode selection (Upload / Live)
- Feature list
- Responsive design

### Upload Mode
- Image upload for front, side, reference
- Reference size input
- Axis selection (width/height)
- Real-time preview
- Results table with confidence scores
- Visualization overlay

### Live Mode
- Real-time camera feed
- Reference capture
- Color-coded alignment feedback
- Auto-capture countdown
- Manual capture button
- Voice guidance toggle
- Feedback log

## 🔒 Security Considerations

### For Production

1. **CORS**: Configure proper CORS origins
```python
CORS(app, origins=['https://yourdomain.com'])
```

2. **HTTPS**: Use SSL certificates
```python
socketio.run(app, ssl_context='adhoc')
```

3. **Authentication & JWT Security**:
```bash
# Generate a secure 32+ byte cryptographic secret
.\venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
# Set in .env or environment:
JWT_SECRET_KEY=your_generated_secret_key_at_least_32_bytes
```
- Changing `JWT_SECRET_KEY` invalidates existing user tokens; users must log in again.
- Never commit secrets to Git.


4. **Rate Limiting**: Prevent abuse
```python
from flask_limiter import Limiter
```

5. **Input Validation**: Validate all inputs
```python
from marshmallow import Schema, fields
```

## 🐛 Troubleshooting

### Backend Issues

**Port already in use**
```bash
# Change port in app.py
socketio.run(app, port=5001)
```

**Models not loading**
```bash
# Check dependencies
pip list | grep torch
pip list | grep mediapipe

# Reinstall if needed
pip install --upgrade torch mediapipe
```

**CUDA errors**
```bash
# Use CPU mode
# In segmentation_model.py:
self.device = 'cpu'
```

### Frontend Issues

**npm install fails**
```bash
# Clear cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**Proxy not working**
```bash
# Check backend is running
curl http://localhost:5000/api/health

# Update proxy in package.json
```

**WebSocket connection fails**
```bash
# Check firewall settings
# Ensure port 5000 is open
```

## 📊 Performance Optimization

### Backend

1. **Use GPU**: Ensure CUDA is available
```python
import torch
print(torch.cuda.is_available())
```

2. **Reduce Model Complexity**: Use lighter models
```python
# In landmark_detector.py
model_complexity=1  # Instead of 2
```

3. **Frame Rate**: Adjust streaming FPS
```python
time.sleep(0.033)  # 30 FPS
time.sleep(0.066)  # 15 FPS (lighter)
```

### Frontend

1. **Image Compression**: Compress before upload
```javascript
// Resize images before sending
canvas.toDataURL('image/jpeg', 0.8)
```

2. **Lazy Loading**: Load components on demand
```javascript
const LiveMode = React.lazy(() => import('./components/LiveMode'));
```

3. **Memoization**: Prevent unnecessary re-renders
```javascript
const MemoizedComponent = React.memo(Component);
```

## 🚢 Deployment

### Backend Deployment (Heroku)

```bash
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Deploy
heroku create your-app-name
git push heroku main
```

### Frontend Deployment (Vercel)

```bash
# Build
npm run build

# Deploy
vercel deploy
```

### Docker Deployment

```dockerfile
# Dockerfile for backend
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

```dockerfile
# Dockerfile for frontend
FROM node:18
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

## 📝 Development Workflow

1. **Start Backend**
```bash
cd backend
venv\Scripts\activate
python app.py
```

2. **Start Frontend** (new terminal)
```bash
cd frontend
npm start
```

3. **Make Changes**
- Backend: Changes auto-reload with Flask debug mode
- Frontend: Changes auto-reload with React hot reload

4. **Test**
- Backend: `pytest tests/`
- Frontend: `npm test`

## 🎓 Usage Examples

### Upload Mode

1. Open `http://localhost:3000`
2. Click "Upload Images"
3. Enter reference size (e.g., 29.7 for A4)
4. Upload reference, front, and side images
5. Click "Process & Measure"
6. View results with confidence scores

### Live Mode

1. Open `http://localhost:3000`
2. Click "Live Camera"
3. Place reference object in frame
4. Enter size and click "Capture Reference"
5. Align body with template
6. Wait for green status
7. Auto-capture or manual capture
8. View measurements

## 🆘 Support

### Common Questions

**Q: Can I run without GPU?**
A: Yes, but slower. Models will use CPU automatically.

**Q: What browsers are supported?**
A: Chrome, Firefox, Safari, Edge (latest versions).

**Q: Can I use on mobile?**
A: Frontend is responsive, but camera features work best on desktop.

**Q: How accurate are measurements?**
A: ±1-2 cm with proper calibration and conditions.

## 📚 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/)
- [MediaPipe Guide](https://google.github.io/mediapipe/)
- [Detectron2 Tutorial](https://detectron2.readthedocs.io/)

---

**Ready to start? Run:** `SETUP_FULLSTACK.bat`
