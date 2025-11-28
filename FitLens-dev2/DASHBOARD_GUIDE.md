## 🎯 Body Measurement Dashboard - Complete Guide

Advanced body measurement system with Upload and Live Camera modes.

## 🌟 Features

### Two Operating Modes

**1. Upload Images Mode**
- Upload front view, side view, and reference object photos
- Process images offline
- Get detailed measurements with confidence scores
- Perfect for batch processing

**2. Live Camera Mode**
- Real-time pose detection and feedback
- Color-coded alignment guidance (Red/Amber/Green)
- Auto-capture after 3 seconds of perfect alignment
- Voice guidance (optional)
- Temporal stability checks with RNN/LSTM

### Advanced Technologies

- **Mask R-CNN**: Instance segmentation for person detection
- **MediaPipe**: High-precision landmark detection (33 points)
- **RNN/LSTM**: Temporal stability analysis
- **Reference Calibration**: Accurate pixel-to-cm conversion
- **TTS**: Voice guidance for hands-free operation

## 📋 Requirements

### Software
- Python 3.11 (recommended)
- Webcam (for Live mode)
- Windows/Linux/macOS

### Dependencies
```bash
pip install opencv-python mediapipe torch torchvision
pip install customtkinter pyttsx3 scikit-image
pip install detectron2  # Optional, for Mask R-CNN
```

## 🚀 Quick Start

### Method 1: Use Launcher (Easiest)
```bash
RUN_DASHBOARD.bat
```

### Method 2: Manual Start
```bash
# Activate virtual environment (if using)
venv311\Scripts\activate

# Install dependencies
pip install -r requirements_rcnn.txt

# Run dashboard
python dashboard_app.py
```

## 📖 User Guide

### Upload Images Mode

#### Step 1: Prepare Images
You need three images:
1. **Front View**: Full body, facing camera, arms slightly away
2. **Side View**: Full body, side profile
3. **Reference Object**: Known-size object (e.g., A4 paper, credit card)

#### Step 2: Enter Reference Size
- Input the known size of your reference object in cm
- Examples:
  - A4 paper height: 29.7 cm
  - A4 paper width: 21.0 cm
  - Credit card width: 8.56 cm
  - Credit card height: 5.398 cm
- Select whether you're measuring width or height

#### Step 3: Upload Images
- Click "Upload Reference Image" and select your reference photo
- Click "Upload Front View" and select front body photo
- Click "Upload Side View" and select side body photo

#### Step 4: Process
- Click "Process & Measure"
- Wait for processing (may take 10-30 seconds)
- View results with measurements and confidence scores

### Live Camera Mode

#### Step 1: Capture Reference
1. Place reference object (e.g., A4 paper) in frame
2. Enter known size in cm
3. Select width or height
4. Click "Capture Reference"
5. Keep reference object visible during measurement

#### Step 2: Align with Template
1. Stand in front of camera
2. Align your body with the semi-transparent outline
3. Follow color-coded feedback:
   - 🔴 **Red**: Major adjustments needed
   - 🟡 **Amber**: Minor adjustments needed
   - 🟢 **Green**: Perfect alignment!

#### Step 3: Auto-Capture
1. When alignment is GREEN, hold still
2. 3-second countdown begins
3. Stay aligned for full 3 seconds
4. Image auto-captures
5. Measurements calculated automatically

#### Step 4: Manual Capture (Optional)
- Click "Manual Capture" button anytime
- Useful if auto-capture isn't triggering

## 🎨 Color-Coded Feedback

### Red Overlay 🔴
**Meaning**: Major corrections needed

**Common Issues**:
- Feet not visible in frame
- Reference object missing or moved
- Large body tilt or rotation
- Too close or too far from camera

**Actions**:
- Step back to show full body
- Ensure reference object is visible
- Stand straight, face camera
- Center yourself in frame

### Amber Overlay 🟡
**Meaning**: Minor adjustments needed

**Common Issues**:
- Slight tilt or rotation
- Arms too close to body
- Not perfectly centered
- Reference object partially occluded

**Actions**:
- Make small position adjustments
- Move arms slightly away from body
- Center yourself better
- Ensure reference is fully visible

### Green Overlay 🟢
**Meaning**: Perfect alignment!

**What Happens**:
- 3-second countdown starts
- Hold position steady
- Auto-capture triggers
- Measurements calculated

**Tips**:
- Stay very still
- Keep breathing normally
- Don't move reference object
- Wait for capture confirmation

## 📏 Measurements Provided

### Front View Measurements
- **Shoulder Width**: Distance between shoulders
- **Hip Width**: Distance between hips
- **Chest Width**: Chest measurement at shoulder level
- **Waist Width**: Waist measurement at hip level
- **Arm Span**: Distance between wrists (arms extended)

### Side View Measurements
- **Torso Depth**: Front-to-back chest depth
- **Shoulder to Hip**: Vertical torso length
- **Hip to Ankle**: Leg length

### Measurement Confidence
Each measurement includes:
- **Value**: Measurement in cm
- **Confidence**: 0-1 score (higher is better)
- **Source**: MediaPipe or Estimated

## 🎤 Voice Guidance

Enable voice guidance for hands-free operation:
- Toggle "Voice Guidance" checkbox
- Provides audio feedback for:
  - Reference capture success/failure
  - Alignment status
  - Capture confirmation
  - Error messages

## 🔧 Reference Object Tips

### Good Reference Objects
✅ **A4 Paper** (29.7 cm height, 21.0 cm width)
- Easy to find
- Large and visible
- Flat and rigid

✅ **Credit Card** (8.56 cm width, 5.398 cm height)
- Standard size worldwide
- Always available
- Easy to hold

✅ **Ruler** (30 cm length)
- Precise measurement
- Easy to position
- Clear markings

### Reference Object Placement
1. **Same Plane**: Place at same distance as your body
2. **Visible**: Keep in frame during entire capture
3. **Stable**: Don't move it during measurement
4. **Flat**: Ensure it's not tilted or curved
5. **Well-Lit**: Good lighting for detection

### Common Reference Sizes
| Object | Width (cm) | Height (cm) |
|--------|-----------|-------------|
| A4 Paper | 21.0 | 29.7 |
| Letter Paper | 21.59 | 27.94 |
| Credit Card | 8.56 | 5.398 |
| Business Card | 8.9 | 5.1 |
| CD Case | 12.4 | 12.4 |

## 🎯 Best Practices

### For Upload Mode
1. **Good Lighting**: Even, bright lighting
2. **Plain Background**: Solid color, no patterns
3. **Full Body**: Entire body visible, head to feet
4. **Arms Away**: Arms slightly away from body
5. **High Resolution**: Use good quality camera
6. **Reference Clear**: Reference object clearly visible

### For Live Mode
1. **Camera Position**: Place camera at chest height
2. **Distance**: Stand 2-3 meters from camera
3. **Lighting**: Face light source, avoid backlighting
4. **Clothing**: Fitted clothing shows body shape better
5. **Reference First**: Always capture reference before body
6. **Stay Still**: Minimize movement during countdown

## ⚙️ Advanced Settings

### Temporal Stability
- **Sequence Length**: 30 frames (1 second at 30 FPS)
- **Stability Threshold**: 0.8 (80% confidence)
- **LSTM Model**: 2-layer, 64 hidden units
- **Smoothing**: 5-frame moving average

### Segmentation
- **Model**: Mask R-CNN (ResNet-50 FPN)
- **Threshold**: 0.5 confidence
- **Fallback**: HSV-based skin detection

### Landmark Detection
- **Model**: MediaPipe Pose (Complexity 2)
- **Points**: 33 body landmarks
- **Confidence**: 0.5 minimum
- **Smoothing**: Enabled

## 🐛 Troubleshooting

### "Reference object not detected"
**Solutions**:
- Ensure object is clearly visible
- Improve lighting
- Use larger reference object
- Hold object flat, not tilted
- Try different background

### "No person detected"
**Solutions**:
- Ensure full body is in frame
- Improve lighting
- Remove background clutter
- Stand closer to camera
- Check camera is working

### Auto-capture not triggering
**Solutions**:
- Hold position very still
- Ensure reference is stable
- Check alignment is GREEN
- Wait full 3 seconds
- Use manual capture instead

### Measurements seem incorrect
**Solutions**:
- Verify reference size is correct
- Ensure reference is same distance as body
- Check reference axis (width vs height)
- Recapture with better alignment
- Use multiple captures and average

### Voice guidance not working
**Solutions**:
- Check system audio is on
- Verify pyttsx3 is installed
- Try toggling voice guidance off/on
- Check Windows speech settings

## 📊 Technical Details

### Architecture
```
Dashboard (UI)
    ├── Upload Mode
    │   ├── Reference Detector
    │   ├── Segmentation Model (Mask R-CNN)
    │   ├── Landmark Detector (MediaPipe)
    │   └── Measurement Engine
    │
    └── Live Mode
        ├── Camera Feed
        ├── Temporal Stabilizer (LSTM)
        ├── Reference Detector
        ├── Segmentation Model
        ├── Landmark Detector
        ├── Alignment Checker
        └── Measurement Engine
```

### Data Flow
```
Image/Frame
    ↓
Segmentation (Mask R-CNN)
    ↓
Landmark Detection (MediaPipe)
    ↓
Temporal Smoothing (LSTM)
    ↓
Reference Calibration
    ↓
Measurement Calculation
    ↓
Results Display
```

## 🔒 Privacy

- **No Cloud Upload**: All processing is local
- **No Data Storage**: Images not saved by default
- **Temporary Only**: Processed data cleared after session
- **User Control**: You control what gets saved

## 📝 Tips for Accurate Measurements

1. **Calibration is Key**: Accurate reference size = accurate measurements
2. **Multiple Captures**: Take 3-5 measurements and average
3. **Consistent Posture**: Use same pose for all captures
4. **Good Lighting**: Even lighting reduces errors
5. **Fitted Clothing**: Shows body shape more clearly
6. **Reference Stability**: Keep reference object still
7. **Full Body Visible**: Ensure feet and head are in frame
8. **Perpendicular**: Stand perpendicular to camera

## 🎓 Example Workflow

### Complete Measurement Session

1. **Setup** (1 minute)
   - Launch dashboard
   - Choose Live Camera mode
   - Position camera at chest height
   - Ensure good lighting

2. **Reference Capture** (30 seconds)
   - Place A4 paper in frame
   - Enter 29.7 cm (height)
   - Click "Capture Reference"
   - Keep paper visible

3. **Body Measurement** (2-3 minutes)
   - Stand 2 meters from camera
   - Align with template outline
   - Wait for GREEN status
   - Hold still for 3 seconds
   - Auto-capture triggers
   - Review measurements

4. **Repeat** (optional)
   - Take 2-3 more captures
   - Average the results
   - Save final measurements

Total Time: ~5 minutes for complete measurement

## 🆘 Support

### Common Questions

**Q: Which mode should I use?**
A: Live mode for real-time feedback, Upload mode for batch processing.

**Q: What's the best reference object?**
A: A4 paper (29.7 cm height) - large, flat, and commonly available.

**Q: How accurate are the measurements?**
A: ±1-2 cm with proper calibration and good conditions.

**Q: Can I use without Detectron2?**
A: Yes, fallback segmentation is available (less accurate).

**Q: Does it work on Mac/Linux?**
A: Yes, cross-platform compatible.

---

**Ready to measure? Run:** `RUN_DASHBOARD.bat`
