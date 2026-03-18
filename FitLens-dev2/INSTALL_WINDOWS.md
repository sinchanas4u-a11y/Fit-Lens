# Windows Installation Guide

Complete guide for installing the Body Measurement application on Windows.

## 🎯 Quick Summary

Detectron2 installation on Windows requires special steps. Choose one of these methods:

1. **Method 1: WSL2** (Recommended - Easiest)
2. **Method 2: Build from Source** (Requires Visual Studio)
3. **Method 3: Pre-built Wheel** (If available for your setup)
4. **Method 4: Use MediaPipe Instead** (Lightweight alternative)

---

## 📋 Prerequisites

### Required
- Windows 10/11
- Python 3.8, 3.9, 3.10, or 3.11 (NOT 3.12+)
- NVIDIA GPU with CUDA support (recommended)
- 8GB+ RAM

### Check Python Version
```bash
python --version
```
**Important:** Detectron2 doesn't support Python 3.12+ yet. Use Python 3.8-3.11.

---

## 🚀 Method 1: WSL2 (Recommended)

This is the **easiest and most reliable** method for Windows users.

### Step 1: Install WSL2

Open PowerShell as Administrator:
```powershell
wsl --install
```

Restart your computer when prompted.

### Step 2: Open Ubuntu (WSL2)

Search for "Ubuntu" in Start Menu and open it.

### Step 3: Install in WSL2

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and pip
sudo apt install python3-pip python3-dev -y

# Install dependencies
sudo apt install git build-essential -y

# Install PyTorch
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install Detectron2
pip3 install 'git+https://github.com/facebookresearch/detectron2.git'

# Install other dependencies
pip3 install opencv-python numpy scipy pillow pycocotools albumentations tqdm pyyaml

# Navigate to your project
cd /mnt/c/path/to/your/project

# Run the application
python3 main.py --demo
```

### Accessing Windows Files from WSL2
Your Windows C: drive is at `/mnt/c/`

Example:
```bash
cd /mnt/c/Users/YourName/Documents/body-measurement
```

---

## 🔧 Method 2: Build from Source (Windows Native)

### Step 1: Install Visual Studio Build Tools

Download and install from:
https://visualstudio.microsoft.com/downloads/

**Required components:**
- Desktop development with C++
- Windows 10 SDK
- MSVC v142 or later

### Step 2: Install PyTorch

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Step 3: Install Git

Download from: https://git-scm.com/download/win

### Step 4: Install Detectron2

Open Command Prompt or PowerShell:
```bash
pip install git+https://github.com/facebookresearch/detectron2.git
```

### Step 5: Install Other Dependencies

```bash
pip install opencv-python numpy scipy pillow pycocotools-windows albumentations tqdm pyyaml fvcore iopath omegaconf hydra-core
```

**Note:** Use `pycocotools-windows` instead of `pycocotools` on Windows.

### Step 6: Test Installation

```bash
python test_installation.py
```

---

## 📦 Method 3: Pre-built Wheel (If Available)

Check if a pre-built wheel exists for your configuration:

### Step 1: Check Your Setup

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.version.cuda}')"
```

### Step 2: Find Matching Wheel

Visit: https://github.com/facebookresearch/detectron2/releases

Look for a wheel matching:
- Your Python version (e.g., cp310 = Python 3.10)
- Your CUDA version (e.g., cu118 = CUDA 11.8)
- Windows (win_amd64)

Example: `detectron2-0.6-cp310-cp310-win_amd64.whl`

### Step 3: Install Wheel

```bash
pip install path/to/downloaded/wheel.whl
```

### Step 4: Install Other Dependencies

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install opencv-python numpy scipy pillow pycocotools-windows albumentations tqdm pyyaml
```

---

## 🎯 Method 4: Use MediaPipe Instead (Lightweight)

If Detectron2 installation is too complex, use the MediaPipe version:

### Step 1: Install Dependencies

```bash
pip install opencv-python mediapipe numpy
```

### Step 2: Run MediaPipe Version

```bash
python pose_capture.py
```

**Note:** MediaPipe version doesn't include body measurements, but provides pose detection and alignment feedback.

---

## 🧪 Verify Installation

### Test 1: Check Imports

```bash
python -c "import torch; import cv2; import numpy; print('Basic imports OK')"
```

### Test 2: Check Detectron2 (if installed)

```bash
python -c "import detectron2; print(f'Detectron2: {detectron2.__version__}')"
```

### Test 3: Run Full Test

```bash
python test_installation.py
```

### Test 4: Run Demo

```bash
python main.py --demo
```

---

## ❌ Common Issues & Solutions

### Issue 1: "No module named 'detectron2'"

**Solution:**
- Detectron2 not installed
- Try Method 1 (WSL2) or Method 4 (MediaPipe)

### Issue 2: "Microsoft Visual C++ 14.0 or greater is required"

**Solution:**
- Install Visual Studio Build Tools (Method 2)
- Or use WSL2 (Method 1)

### Issue 3: "Could not find a version that satisfies the requirement detectron2"

**Solution:**
- Pre-built wheels not available for your setup
- Use Method 1 (WSL2) or Method 2 (Build from source)

### Issue 4: Python 3.12 compatibility

**Solution:**
- Detectron2 doesn't support Python 3.12 yet
- Downgrade to Python 3.10 or 3.11
- Or use virtual environment with older Python

### Issue 5: CUDA not available

**Solution:**
- Install CUDA Toolkit from NVIDIA
- Or use CPU version (slower):
  ```bash
  pip install torch torchvision
  ```

### Issue 6: "pycocotools" installation fails

**Solution:**
- Use `pycocotools-windows` instead:
  ```bash
  pip install pycocotools-windows
  ```

---

## 🎓 Recommended Setup for Windows Users

### Best Option: WSL2 + GPU

1. Install WSL2
2. Install CUDA in WSL2:
   ```bash
   wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
   sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
   sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/3bf863cc.pub
   sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/ /"
   sudo apt-get update
   sudo apt-get -y install cuda
   ```
3. Follow Method 1 steps

### Alternative: MediaPipe (No Detectron2 needed)

If you just need pose detection without measurements:
1. Use `pose_capture.py` instead
2. Much easier installation
3. Faster performance
4. No CUDA required

---

## 📊 Installation Time Estimates

| Method | Time | Difficulty | Reliability |
|--------|------|------------|-------------|
| WSL2 | 30 min | Easy | ⭐⭐⭐⭐⭐ |
| Build from Source | 1-2 hours | Hard | ⭐⭐⭐ |
| Pre-built Wheel | 10 min | Easy | ⭐⭐⭐⭐ |
| MediaPipe | 5 min | Very Easy | ⭐⭐⭐⭐⭐ |

---

## 🔍 Step-by-Step Troubleshooting

### If installation fails:

1. **Check Python version**
   ```bash
   python --version
   ```
   Must be 3.8-3.11

2. **Check pip version**
   ```bash
   pip --version
   ```
   Update if needed: `python -m pip install --upgrade pip`

3. **Check PyTorch installation**
   ```bash
   python -c "import torch; print(torch.__version__)"
   ```

4. **Check CUDA availability**
   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```

5. **Try MediaPipe version**
   ```bash
   pip install opencv-python mediapipe numpy
   python pose_capture.py
   ```

---

## 💡 Pro Tips

### Tip 1: Use Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements_rcnn.txt
```

### Tip 2: Use Conda (Alternative)

```bash
conda create -n body-measure python=3.10
conda activate body-measure
conda install pytorch torchvision pytorch-cuda=11.8 -c pytorch -c nvidia
pip install git+https://github.com/facebookresearch/detectron2.git
```

### Tip 3: Check GPU Usage

```bash
nvidia-smi
```

### Tip 4: Use CPU if GPU fails

Edit `config.py`:
```python
# Force CPU usage
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
```

---

## 📞 Still Having Issues?

1. **Try WSL2** - Most reliable for Windows
2. **Try MediaPipe version** - No Detectron2 needed
3. **Check Python version** - Must be 3.8-3.11
4. **Use virtual environment** - Avoid conflicts
5. **Check error messages** - Google specific errors

---

## ✅ Success Checklist

- [ ] Python 3.8-3.11 installed
- [ ] PyTorch installed
- [ ] Detectron2 installed (or using MediaPipe)
- [ ] Other dependencies installed
- [ ] `python test_installation.py` passes
- [ ] `python main.py --demo` works
- [ ] Camera accessible

---

## 🚀 Quick Start After Installation

```bash
# Test installation
python test_installation.py

# Run demo (no camera)
python main.py --demo

# Run with camera
python main.py --height 175
```

---

**Recommended: Use WSL2 for the best Windows experience!**
