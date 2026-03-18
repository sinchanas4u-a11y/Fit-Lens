# Quick Fix Guide

## 🔴 Got an Error? Start Here!

### Step 1: Check Your Python Version

```bash
python --version
```

**If you see Python 3.12.x:**
- ❌ Not compatible with Detectron2
- ✅ **Solution:** See [PYTHON_VERSION_FIX.md](PYTHON_VERSION_FIX.md)
- ✅ **Quick Alternative:** Use MediaPipe version

**If you see Python 3.8-3.11:**
- ✅ Compatible! Continue to Step 2

### Step 2: Run Diagnostic

```bash
python check_detectron2.py
```

This will tell you exactly what's wrong and what to do.

---

## 🎯 Common Errors & Quick Fixes

### Error: "operator torchvision::nms does not exist"

**Cause:** Python 3.12 incompatibility

**Quick Fix:**
```bash
# Option 1: Use MediaPipe (works immediately)
pip install opencv-python mediapipe numpy
python pose_capture.py

# Option 2: Install Python 3.11
# See PYTHON_VERSION_FIX.md
```

### Error: "Could not find a version that satisfies the requirement detectron2"

**Cause:** Detectron2 installation issue

**Quick Fix:**
```bash
# Option 1: Install from source
pip install git+https://github.com/facebookresearch/detectron2.git

# Option 2: Use MediaPipe instead
pip install mediapipe
python pose_capture.py

# Option 3: Windows - Use WSL2
# See INSTALL_WINDOWS.md
```

### Error: "Microsoft Visual C++ 14.0 or greater is required"

**Cause:** Windows build tools missing

**Quick Fix:**
```bash
# Option 1: Use WSL2 (easiest)
wsl --install
# See INSTALL_WINDOWS.md

# Option 2: Install Visual Studio Build Tools
# Download from: https://visualstudio.microsoft.com/downloads/

# Option 3: Use MediaPipe (no build tools needed)
pip install mediapipe
python pose_capture.py
```

### Error: "No module named 'cv2'" or "No module named 'detectron2'"

**Cause:** Dependencies not installed in current Python environment

**Quick Fix:**
```bash
# Option 1: Use launcher (easiest)
RUN_MEDIAPIPE.bat

# Option 2: Activate virtual environment
venv311\Scripts\activate
pip install opencv-python mediapipe numpy

# Option 3: Install in current Python
pip install opencv-python mediapipe numpy
python pose_capture.py
```

See [FIX_CV2_ERROR.md](FIX_CV2_ERROR.md) for details.

---

## 🚀 Fastest Solution (Works Immediately)

**Use the MediaPipe version - no complex setup needed:**

```bash
# Install (takes 1 minute)
pip install opencv-python mediapipe numpy

# Run
python pose_capture.py
```

**What you get:**
- ✅ Real-time pose detection
- ✅ RED/GREEN skeleton feedback
- ✅ Alignment checking
- ✅ Auto-capture
- ✅ Works with Python 3.12
- ✅ No Detectron2 needed
- ✅ No build tools needed
- ❌ No body measurements (R-CNN feature)

---

## 📋 Full R-CNN Setup (With Measurements)

### For Python 3.8-3.11:

```bash
# 1. Install PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# 2. Install dependencies
pip install opencv-python numpy scipy pillow albumentations tqdm pyyaml

# 3. Windows: Use pycocotools-windows
pip install pycocotools-windows

# 4. Install Detectron2
pip install git+https://github.com/facebookresearch/detectron2.git

# 5. Test
python check_detectron2.py
python test_installation.py

# 6. Run
python main.py --height 175
```

### For Python 3.12:

**You need to use Python 3.11. Two options:**

**Option A: Virtual Environment**
```bash
# Install Python 3.11 from python.org
# Then create venv
py -3.11 -m venv venv311
venv311\Scripts\activate
# Now follow steps above
```

**Option B: Use Conda**
```bash
conda create -n body-measure python=3.11
conda activate body-measure
# Now follow steps above
```

See [PYTHON_VERSION_FIX.md](PYTHON_VERSION_FIX.md) for details.

---

## 🔍 Diagnostic Commands

```bash
# Check Python version
python --version

# Check what's installed
python check_detectron2.py

# Test full installation
python test_installation.py

# Try demo mode (no camera)
python main.py --demo

# Try MediaPipe version
python pose_capture.py
```

---

## 📚 Detailed Guides

| Issue | Guide |
|-------|-------|
| Python 3.12 | [PYTHON_VERSION_FIX.md](PYTHON_VERSION_FIX.md) |
| Windows Installation | [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md) |
| Detectron2 Issues | [DETECTRON2_FIX.md](DETECTRON2_FIX.md) |
| Quick Start | [QUICKSTART.md](QUICKSTART.md) |
| Full Documentation | [README_RCNN.md](README_RCNN.md) |

---

## 🎯 Decision Tree

```
Start
  │
  ▼
Check Python Version
  │
  ├─ Python 3.12? ──► See PYTHON_VERSION_FIX.md
  │                   Or use MediaPipe
  │
  └─ Python 3.8-3.11? ──► Continue
                          │
                          ▼
                    Install PyTorch
                          │
                          ▼
                    Install Detectron2
                          │
                          ├─ Success? ──► Run main.py
                          │
                          └─ Failed? ──► Windows? ──► See INSTALL_WINDOWS.md
                                         │
                                         └─ Linux/Mac? ──► See DETECTRON2_FIX.md
```

---

## ✅ Success Checklist

Run these commands. All should work:

```bash
# 1. Python version
python --version  # Should be 3.8-3.11

# 2. Check installation
python check_detectron2.py  # Should show all ✓

# 3. Test installation
python test_installation.py  # Should pass all tests

# 4. Try demo
python main.py --demo  # Should show synthetic pose

# 5. Try with camera
python main.py --height 175  # Should open camera
```

---

## 🆘 Still Stuck?

1. **Run diagnostic:**
   ```bash
   python check_detectron2.py
   ```

2. **Check Python version:**
   ```bash
   python --version
   ```
   Must be 3.8-3.11 for R-CNN version

3. **Use MediaPipe (always works):**
   ```bash
   pip install mediapipe
   python pose_capture.py
   ```

4. **Read detailed guides:**
   - Python 3.12: [PYTHON_VERSION_FIX.md](PYTHON_VERSION_FIX.md)
   - Windows: [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md)
   - Detectron2: [DETECTRON2_FIX.md](DETECTRON2_FIX.md)

---

**Most Common Issue:** Python 3.12 → Use Python 3.11 or MediaPipe version
