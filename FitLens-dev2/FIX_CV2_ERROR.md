# Fix: ModuleNotFoundError: No module named 'cv2'

## 🔴 Problem

The error `ModuleNotFoundError: No module named 'cv2'` means OpenCV is not installed in the Python environment you're using.

## ✅ Quick Solutions

### Solution 1: Use the Launcher Script (EASIEST)

Just double-click this file:
```
RUN_APP.bat
```

This will:
- Activate the correct Python environment
- Install missing dependencies
- Run the application

### Solution 2: Activate Virtual Environment Manually

You have a Python 3.11 virtual environment (`venv311`). Activate it first:

```bash
# Activate the virtual environment
venv311\Scripts\activate

# Verify Python version
python --version  # Should show Python 3.11.x

# Install OpenCV
pip install opencv-python

# Install other dependencies
pip install numpy mediapipe

# Run the application
python pose_capture.py
```

### Solution 3: Install in Global Python 3.12

If you want to use your global Python 3.12:

```bash
# Install OpenCV
pip install opencv-python

# Install MediaPipe
pip install mediapipe numpy

# Run MediaPipe version (works with Python 3.12)
python pose_capture.py
```

**Note:** For the R-CNN version (`main.py`), you MUST use Python 3.11 (see Solution 2).

## 🎯 Which Solution to Use?

| Your Goal | Solution |
|-----------|----------|
| Just want it to work | Solution 1 (RUN_APP.bat) |
| Want to understand | Solution 2 (Manual activation) |
| Using Python 3.12 | Solution 3 (Global install) |

## 📋 Step-by-Step Fix

### For MediaPipe Version (Easiest)

1. **Open Command Prompt in your project folder**

2. **Install OpenCV:**
   ```bash
   pip install opencv-python mediapipe numpy
   ```

3. **Run the app:**
   ```bash
   python pose_capture.py
   ```

### For R-CNN Version (Requires Python 3.11)

1. **Activate virtual environment:**
   ```bash
   venv311\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install opencv-python numpy scipy pillow albumentations tqdm pyyaml
   ```

3. **Install PyTorch:**
   ```bash
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

4. **Install Detectron2:**
   ```bash
   pip install git+https://github.com/facebookresearch/detectron2.git
   ```

5. **Run the app:**
   ```bash
   python main.py --demo
   ```

## 🔍 Verify Installation

Check if OpenCV is installed:

```bash
python -c "import cv2; print(f'OpenCV version: {cv2.__version__}')"
```

If this works, OpenCV is installed correctly.

## ❌ Common Issues

### Issue 1: "pip is not recognized"

**Solution:**
```bash
python -m pip install opencv-python
```

### Issue 2: Virtual environment not activating

**Solution:**
```bash
# Make sure you're in the project folder
cd C:\Users\sinch\OneDrive\Desktop\FitLens

# Then activate
venv311\Scripts\activate
```

### Issue 3: Wrong Python version

**Solution:**
```bash
# Check which Python you're using
python --version

# If it's 3.12 and you need 3.11:
venv311\Scripts\activate
python --version  # Should now show 3.11
```

## 🚀 Quick Commands

### Just Run MediaPipe Version:
```bash
pip install opencv-python mediapipe numpy
python pose_capture.py
```

### Run with Virtual Environment:
```bash
venv311\Scripts\activate
pip install opencv-python mediapipe numpy
python pose_capture.py
```

### Use the Launcher:
```bash
RUN_APP.bat
```

## 💡 Understanding the Issue

You have two Python installations:
1. **Global Python 3.12** - at `C:\Users\sinch\AppData\Local\Programs\Python\Python312`
2. **Virtual Environment Python 3.11** - at `venv311`

When you run `python main.py`, it uses whichever Python is active. If you haven't activated `venv311`, it uses global Python 3.12, which might not have all dependencies.

**Solution:** Always activate the virtual environment first!

## ✅ Recommended Workflow

1. **Open Command Prompt**
2. **Navigate to project:**
   ```bash
   cd C:\Users\sinch\OneDrive\Desktop\FitLens
   ```
3. **Activate venv:**
   ```bash
   venv311\Scripts\activate
   ```
4. **Run app:**
   ```bash
   python pose_capture.py
   ```

Or just use:
```bash
RUN_APP.bat
```

---

**Bottom Line:** Activate `venv311` first, or use `RUN_APP.bat`!
