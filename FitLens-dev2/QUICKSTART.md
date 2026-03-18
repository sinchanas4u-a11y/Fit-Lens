# Quick Start Guide

Get up and running in 5 minutes!

## 🚀 Installation (Windows)

### 1. Install Python 3.8+
Download from [python.org](https://www.python.org/downloads/)

### 2. Install PyTorch with CUDA

Open Command Prompt or PowerShell:

```bash
# For NVIDIA GPU (CUDA 11.8)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# For CPU only (slower)
pip install torch torchvision
```

### 3. Install Detectron2

**Windows Users:** See [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md) for detailed instructions.

**Linux/Mac:**
```bash
pip install git+https://github.com/facebookresearch/detectron2.git
```

**If Detectron2 fails:** Use the MediaPipe version instead (no Detectron2 needed):
```bash
pip install opencv-python mediapipe numpy
python pose_capture.py
```

### 4. Install Other Dependencies

```bash
pip install -r requirements_rcnn.txt
```

## 🎮 Run the Application

### Basic Usage (Pretrained Model)

```bash
python main.py
```

### With Height Calibration (More Accurate)

```bash
python main.py --height 175
```
Replace `175` with your height in centimeters.

### Demo Mode (No Camera Required)

```bash
python main.py --demo
```

## 📖 How to Use

1. **Launch the application**
   ```bash
   python main.py
   ```

2. **Position yourself**
   - Stand 2 meters from camera
   - Face the camera directly
   - Ensure full body is visible

3. **Follow the on-screen guidance**
   - Skeleton will be **RED** when misaligned
   - Skeleton will be **GREEN** when aligned
   - Read feedback messages:
     - "Move left/right" - adjust horizontal position
     - "Move closer/back" - adjust distance
     - "Straighten arms" - extend arms
     - "Move arms away from body" - create space

4. **Hold the pose**
   - When skeleton turns GREEN, hold still
   - Progress bar shows countdown (90 frames / 3 seconds)
   - Application auto-captures 3 images

5. **View results**
   - Measurements displayed in real-time
   - Final averages shown after all captures
   - Press any key to view captured images

## ⌨️ Keyboard Controls

- **Q**: Quit application
- **R**: Reset captures and start over

## 🎯 Target Pose

For best results:
- Stand straight, facing camera
- Arms slightly away from body (not touching sides)
- Elbows relatively straight (not bent)
- Centered in frame
- Good lighting

## ⚠️ Common Issues

### "Could not open camera"
- Close other applications using the camera
- Try changing camera index in `config.py`: `CAMERA_INDEX = 1`

### "No person detected"
- Ensure full body is visible
- Improve lighting
- Move closer to camera
- Check camera is working

### Slow performance
- Use GPU instead of CPU
- Close other applications
- Reduce resolution in `config.py`

### Detectron2 installation fails
- Install Visual Studio Build Tools
- Or use pre-built wheel (see installation step 3)
- Or use WSL2 on Windows

## 📊 Understanding Measurements

The application measures:
- **Shoulder Width**: Distance between shoulders
- **Arm Length**: Shoulder → Elbow → Wrist
- **Torso Length**: Neck → Hip center
- **Hip Width**: Distance between hips
- **Leg Length**: Hip → Knee → Ankle

Measurements are in **centimeters** and averaged across 3 captures for accuracy.

## 🔧 Customization

Edit `config.py` to adjust:

```python
# Number of images to capture
AUTO_CAPTURE_COUNT = 3

# Frames to hold pose
STABILITY_FRAMES = 30

# Alignment sensitivity (0-1, lower = more lenient)
ALIGNMENT_THRESHOLD = 0.85

# Enable/disable image saving
SAVE_IMAGES = False  # Privacy: disabled by default
```

## 🎓 Training Your Own Model

### Quick Training (COCO Dataset)

1. **Download COCO 2017**
   ```bash
   mkdir -p datasets/coco
   cd datasets/coco
   # Download from http://cocodataset.org/#download
   ```

2. **Start Training**
   ```bash
   python train.py --mode train
   ```

3. **Use Trained Model**
   ```bash
   python main.py --weights output/checkpoints/model_final.pth
   ```

## 📚 Next Steps

- Read full documentation: `README_RCNN.md`
- Explore configuration: `config.py`
- Check code structure: `main.py`, `model_arch.py`, `pose_utils.py`
- Train custom model: `train.py`

## 💡 Tips for Best Results

1. **Lighting**: Ensure even, bright lighting
2. **Background**: Plain background works best
3. **Clothing**: Fitted clothing shows body shape better
4. **Distance**: Stand 1.5-2.5 meters from camera
5. **Calibration**: Provide your height for accurate measurements
6. **Stability**: Hold pose very still during countdown

## 🆘 Need Help?

1. Check `README_RCNN.md` for detailed documentation
2. Review troubleshooting section
3. Verify all dependencies installed correctly
4. Test with demo mode: `python main.py --demo`

---

**Ready to start? Run:** `python main.py`
