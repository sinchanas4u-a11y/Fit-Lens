# Detectron2 Installation Fix

## 🔧 Problem

Installation errors occur because:
1. **Python 3.12+** isn't supported yet (most common issue)
2. Pre-built wheels aren't available for all configurations
3. Windows requires special installation steps

**Check your Python version first:**
```bash
python --version
```

If you see Python 3.12.x, see [PYTHON_VERSION_FIX.md](PYTHON_VERSION_FIX.md)

## ✅ Solutions

### Solution 1: Use WSL2 (RECOMMENDED for Windows)

**Easiest and most reliable method:**

```bash
# In PowerShell (as Administrator)
wsl --install

# Restart computer, then open Ubuntu
# In Ubuntu terminal:
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip3 install 'git+https://github.com/facebookresearch/detectron2.git'
pip3 install opencv-python numpy scipy pillow pycocotools albumentations tqdm pyyaml
```

**See [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md) for complete guide.**

### Solution 2: Install from Source (Windows Native)

**Requirements:**
- Visual Studio Build Tools
- Git
- Python 3.8-3.11 (NOT 3.12)

```bash
# Install PyTorch first
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install Detectron2 from source
pip install git+https://github.com/facebookresearch/detectron2.git

# Install other dependencies
pip install opencv-python numpy scipy pillow pycocotools-windows albumentations tqdm pyyaml
```

### Solution 3: Use MediaPipe Instead (NO Detectron2 needed)

**Fastest solution - works immediately:**

```bash
# Install MediaPipe
pip install opencv-python mediapipe numpy

# Run MediaPipe version
python pose_capture.py
```

**Note:** MediaPipe version doesn't include body measurements, but provides:
- ✓ Real-time pose detection
- ✓ Alignment feedback
- ✓ Auto-capture
- ✓ Much faster installation
- ✓ Works on any system

### Solution 4: Check Your Setup

```bash
# Run this to check what's available
python check_detectron2.py
```

This will tell you:
- If Detectron2 is installed
- If PyTorch is installed
- If MediaPipe is available
- What to do next

## 🎯 Quick Decision Guide

**Choose based on your needs:**

| Need | Solution |
|------|----------|
| Full measurements + training | Solution 1 (WSL2) |
| Windows native | Solution 2 (Build from source) |
| Quick setup, no measurements | Solution 3 (MediaPipe) |
| Not sure what to do | Run `python check_detectron2.py` |

## 📋 Updated Installation Steps

### Step 1: Install PyTorch

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Step 2: Install Other Dependencies

```bash
pip install opencv-python numpy scipy pillow albumentations tqdm pyyaml
```

**Windows:** Use `pycocotools-windows` instead of `pycocotools`
```bash
pip install pycocotools-windows
```

**Linux/Mac:**
```bash
pip install pycocotools
```

### Step 3: Install Detectron2 (Choose One)

**Option A: WSL2 (Windows - Recommended)**
- See [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md)

**Option B: From Source**
```bash
pip install git+https://github.com/facebookresearch/detectron2.git
```

**Option C: Skip Detectron2, Use MediaPipe**
```bash
pip install mediapipe
python pose_capture.py
```

### Step 4: Verify Installation

```bash
# Check what's installed
python check_detectron2.py

# Run full test
python test_installation.py

# Try demo mode
python main.py --demo
```

## 🔍 Troubleshooting

### Error: "Microsoft Visual C++ 14.0 or greater is required"

**Solution:** Install Visual Studio Build Tools
- Download: https://visualstudio.microsoft.com/downloads/
- Or use WSL2

### Error: "No module named 'detectron2'"

**Solution:** Detectron2 not installed
```bash
python check_detectron2.py  # Check status
```

### Error: Python 3.12 compatibility

**Solution:** Detectron2 doesn't support Python 3.12 yet
- Use Python 3.10 or 3.11
- Or use MediaPipe version

### Error: CUDA not available

**Solution:** 
- Install CUDA Toolkit from NVIDIA
- Or use CPU version (slower)
- Or use MediaPipe (works without CUDA)

## 📚 Documentation

- **Windows Guide:** [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md)
- **Quick Start:** [QUICKSTART.md](QUICKSTART.md)
- **Full Guide:** [README_RCNN.md](README_RCNN.md)
- **Check Status:** Run `python check_detectron2.py`

## 🚀 Recommended Path

1. **Run check script:**
   ```bash
   python check_detectron2.py
   ```

2. **Follow recommendations** from the script

3. **If Detectron2 fails:**
   - Windows: Use WSL2 (see INSTALL_WINDOWS.md)
   - Or use MediaPipe: `python pose_capture.py`

4. **Verify:**
   ```bash
   python test_installation.py
   python main.py --demo
   ```

## ✅ Success Criteria

After installation, these should work:

```bash
# Check imports
python -c "import torch; import cv2; import numpy; print('OK')"

# Check Detectron2 (if installed)
python -c "import detectron2; print('Detectron2 OK')"

# Or check MediaPipe (alternative)
python -c "import mediapipe; print('MediaPipe OK')"

# Run demo
python main.py --demo
```

---

**Bottom Line:** If Detectron2 is too complex, use MediaPipe version - it works great for pose detection!
