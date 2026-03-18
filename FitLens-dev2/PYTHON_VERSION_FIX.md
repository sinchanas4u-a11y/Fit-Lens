# Python 3.12 Compatibility Fix

## 🔴 Problem

The error `RuntimeError: operator torchvision::nms does not exist` occurs because:
- **You're using Python 3.12**
- PyTorch/torchvision don't fully support Python 3.12 yet
- Detectron2 doesn't support Python 3.12

## ✅ Solutions

### Solution 1: Downgrade to Python 3.11 (RECOMMENDED)

**This is the easiest and most reliable solution.**

#### Option A: Install Python 3.11 alongside Python 3.12

1. **Download Python 3.11:**
   - Visit: https://www.python.org/downloads/
   - Download Python 3.11.x (latest 3.11 version)
   - Install it (don't uninstall Python 3.12)

2. **Create virtual environment with Python 3.11:**
   ```bash
   # Use py launcher to specify version
   py -3.11 -m venv venv311
   
   # Activate it
   venv311\Scripts\activate
   
   # Verify version
   python --version  # Should show Python 3.11.x
   ```

3. **Install dependencies:**
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   pip install -r requirements_rcnn.txt
   pip install git+https://github.com/facebookresearch/detectron2.git
   ```

#### Option B: Use Conda (Recommended for managing Python versions)

```bash
# Install Miniconda from: https://docs.conda.io/en/latest/miniconda.html

# Create environment with Python 3.11
conda create -n body-measure python=3.11
conda activate body-measure

# Install PyTorch
conda install pytorch torchvision pytorch-cuda=11.8 -c pytorch -c nvidia

# Install other dependencies
pip install -r requirements_rcnn.txt
pip install git+https://github.com/facebookresearch/detectron2.git
```

### Solution 2: Use MediaPipe (Works with Python 3.12)

**MediaPipe supports Python 3.12 and works immediately:**

```bash
# Install MediaPipe (works with Python 3.12)
pip install opencv-python mediapipe numpy

# Run MediaPipe version
python pose_capture.py
```

**Note:** MediaPipe version doesn't include body measurements, but provides:
- ✓ Real-time pose detection
- ✓ Alignment feedback
- ✓ Auto-capture
- ✓ Works with Python 3.12
- ✓ No Detectron2 needed

### Solution 3: Wait for Python 3.12 Support

PyTorch and Detectron2 are working on Python 3.12 support, but it's not ready yet.

**Check current status:**
- PyTorch: https://github.com/pytorch/pytorch/issues
- Detectron2: https://github.com/facebookresearch/detectron2/issues

## 🎯 Quick Decision Guide

| Your Situation | Best Solution |
|----------------|---------------|
| Need full R-CNN features | Solution 1 (Python 3.11) |
| Want quick setup | Solution 2 (MediaPipe) |
| Must use Python 3.12 | Solution 2 (MediaPipe) |
| Comfortable with Conda | Solution 1B (Conda) |

## 📋 Step-by-Step Fix (Python 3.11 with venv)

### Step 1: Check Current Python Version

```bash
python --version
```

If it shows Python 3.12.x, continue with the fix.

### Step 2: Install Python 3.11

1. Download from: https://www.python.org/downloads/release/python-3119/
2. Run installer
3. Check "Add Python 3.11 to PATH" (optional)
4. Complete installation

### Step 3: Create Virtual Environment

```bash
# Navigate to your project folder
cd path\to\your\project

# Create venv with Python 3.11
py -3.11 -m venv venv311

# Activate it
venv311\Scripts\activate

# Verify
python --version  # Should show 3.11.x
```

### Step 4: Install Dependencies

```bash
# Install PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
pip install opencv-python numpy scipy pillow albumentations tqdm pyyaml fvcore iopath omegaconf hydra-core

# Windows: Use pycocotools-windows
pip install pycocotools-windows

# Install Detectron2
pip install git+https://github.com/facebookresearch/detectron2.git
```

### Step 5: Verify Installation

```bash
# Check Python version
python --version

# Check PyTorch
python -c "import torch; print(f'PyTorch: {torch.__version__}')"

# Check torchvision
python -c "import torchvision; print(f'torchvision: {torchvision.__version__}')"

# Run check script
python check_detectron2.py

# Test installation
python test_installation.py
```

## 🔧 Using Conda (Alternative Method)

### Step 1: Install Miniconda

Download from: https://docs.conda.io/en/latest/miniconda.html

### Step 2: Create Environment

```bash
# Create environment with Python 3.11
conda create -n body-measure python=3.11 -y

# Activate
conda activate body-measure

# Verify
python --version
```

### Step 3: Install PyTorch

```bash
# Install PyTorch with CUDA
conda install pytorch torchvision pytorch-cuda=11.8 -c pytorch -c nvidia -y
```

### Step 4: Install Other Dependencies

```bash
# Install from pip
pip install opencv-python scipy pillow albumentations tqdm pyyaml
pip install pycocotools-windows  # Windows
pip install fvcore iopath omegaconf hydra-core

# Install Detectron2
pip install git+https://github.com/facebookresearch/detectron2.git
```

### Step 5: Use the Environment

```bash
# Always activate before use
conda activate body-measure

# Run application
python main.py --demo
```

## 🚀 Quick MediaPipe Alternative

If you just want to get started immediately:

```bash
# Works with Python 3.12!
pip install opencv-python mediapipe numpy

# Run MediaPipe version
python pose_capture.py
```

This gives you:
- ✓ Real-time pose detection
- ✓ RED/GREEN skeleton feedback
- ✓ Alignment checking
- ✓ Auto-capture
- ✓ Works immediately
- ✗ No body measurements (R-CNN feature)

## 📊 Python Version Compatibility

| Component | Python 3.8 | Python 3.9 | Python 3.10 | Python 3.11 | Python 3.12 |
|-----------|------------|------------|-------------|-------------|-------------|
| PyTorch | ✅ | ✅ | ✅ | ✅ | ⚠️ Limited |
| torchvision | ✅ | ✅ | ✅ | ✅ | ⚠️ Limited |
| Detectron2 | ✅ | ✅ | ✅ | ✅ | ❌ No |
| MediaPipe | ✅ | ✅ | ✅ | ✅ | ✅ Yes |

**Recommendation:** Use Python 3.11 for best compatibility.

## ❌ Common Errors with Python 3.12

### Error 1: "operator torchvision::nms does not exist"
**Cause:** Python 3.12 incompatibility  
**Fix:** Use Python 3.11 or MediaPipe

### Error 2: "No module named 'distutils'"
**Cause:** Python 3.12 removed distutils  
**Fix:** Use Python 3.11

### Error 3: Detectron2 installation fails
**Cause:** No Python 3.12 support yet  
**Fix:** Use Python 3.11 or MediaPipe

## 🔍 Verify Your Setup

Run this to check everything:

```bash
python --version
python -c "import sys; print(f'Python: {sys.version}')"
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import torchvision; print(f'torchvision: {torchvision.__version__}')"
python check_detectron2.py
```

## 💡 Pro Tips

### Tip 1: Use Virtual Environments

Always use virtual environments to avoid conflicts:
```bash
# venv method
py -3.11 -m venv venv311
venv311\Scripts\activate

# Or conda method
conda create -n body-measure python=3.11
conda activate body-measure
```

### Tip 2: Check Python Version in Scripts

Add this to your scripts:
```python
import sys
if sys.version_info >= (3, 12):
    print("Warning: Python 3.12 not fully supported")
    print("Recommended: Python 3.11")
```

### Tip 3: Use py Launcher (Windows)

```bash
# List installed Python versions
py --list

# Use specific version
py -3.11 script.py
```

### Tip 4: Keep Both Versions

You can keep Python 3.12 for other projects and use 3.11 for this one via virtual environments.

## 📞 Still Having Issues?

1. **Verify Python version:**
   ```bash
   python --version
   ```
   Must be 3.11 or lower for R-CNN version.

2. **Use MediaPipe if stuck:**
   ```bash
   pip install mediapipe
   python pose_capture.py
   ```

3. **Check virtual environment:**
   Make sure you activated the correct venv.

4. **Try Conda:**
   Often easier for managing Python versions.

## ✅ Success Checklist

- [ ] Python 3.11 installed
- [ ] Virtual environment created
- [ ] Virtual environment activated
- [ ] `python --version` shows 3.11.x
- [ ] PyTorch installed
- [ ] torchvision installed
- [ ] No "nms" error
- [ ] `python check_detectron2.py` passes
- [ ] `python test_installation.py` passes

---

**Bottom Line:** Use Python 3.11 for R-CNN version, or use MediaPipe version with Python 3.12.
