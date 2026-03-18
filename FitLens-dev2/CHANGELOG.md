# Changelog

## Version 1.1 - Auto-Capture Timing Update

### Changed
- **Auto-capture timing increased from 2 seconds to 3 seconds**
  - MediaPipe version: `stability_duration = 3.0` seconds
  - R-CNN version: `STABILITY_FRAMES = 90` frames (3 seconds at 30 FPS)
  
### Reason
- Gives users more time to stabilize their pose
- Reduces false captures from brief alignments
- Improves capture quality

### Files Updated
- `pose_capture.py` - Changed default `stability_duration` from 2.0 to 3.0
- `config.py` - Changed `STABILITY_FRAMES` from 30 to 90
- `README.md` - Updated documentation
- `README_RCNN.md` - Updated documentation
- `README_COMPLETE.md` - Updated documentation
- `QUICKSTART.md` - Updated documentation
- `PROJECT_SUMMARY.md` - Updated documentation

### How It Works

**MediaPipe Version:**
```python
# User must hold aligned pose for 3 seconds
app = PoseAlignmentCapture(target_images=5, stability_duration=3.0)
```

**R-CNN Version:**
```python
# User must hold aligned pose for 90 frames (3 seconds at 30 FPS)
Config.STABILITY_FRAMES = 90
```

### User Experience

**Before (2 seconds):**
- Faster captures
- Sometimes captured before user was fully stable
- Required 60 frames of alignment

**After (3 seconds):**
- More time to stabilize
- Better quality captures
- Requires 90 frames of alignment
- More forgiving for users

### Configuration

Users can still customize the timing:

**MediaPipe:**
```python
# In pose_capture.py main() function
app = PoseAlignmentCapture(
    target_images=5, 
    stability_duration=3.0  # Change this value
)
```

**R-CNN:**
```python
# In config.py
STABILITY_FRAMES = 90  # Change this value (frames at 30 FPS)
```

---

## Version 1.0 - Initial Release

### Features
- Real-time pose detection using R-CNN/MediaPipe
- Color-coded skeleton feedback (RED/GREEN)
- Directional guidance
- Auto-capture on alignment
- Body measurements (R-CNN version)
- Privacy-first design
- Complete documentation

### Components
- Main application (main.py)
- Model architecture (model_arch.py)
- Pose utilities (pose_utils.py)
- Dataset handling (dataset.py)
- Training script (train.py)
- Configuration (config.py)
- MediaPipe alternative (pose_capture.py)

### Documentation
- Complete user guide (README_RCNN.md)
- Quick start guide (QUICKSTART.md)
- Architecture documentation (ARCHITECTURE.md)
- Windows installation guide (INSTALL_WINDOWS.md)
- Python version fix guide (PYTHON_VERSION_FIX.md)
- Detectron2 fix guide (DETECTRON2_FIX.md)
- Quick fix guide (QUICK_FIX.md)
- Visual guide (VISUAL_GUIDE.md)
- Project summary (PROJECT_SUMMARY.md)
- Comparison guide (COMPARISON.md)
