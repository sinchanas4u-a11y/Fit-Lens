@echo off
echo ============================================================
echo Body Measurement Application - Installation Script
echo ============================================================
echo.

echo Step 1: Installing PyTorch with CUDA 11.8...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
if %errorlevel% neq 0 (
    echo ERROR: PyTorch installation failed
    pause
    exit /b 1
)
echo.

echo Step 2: Installing Detectron2...
echo Trying method 1: From source (requires git)...
pip install git+https://github.com/facebookresearch/detectron2.git
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Git installation failed. Trying alternative method...
    echo.
    echo MANUAL INSTALLATION REQUIRED:
    echo 1. Install Visual Studio Build Tools from:
    echo    https://visualstudio.microsoft.com/downloads/
    echo 2. Or use WSL2 (Windows Subsystem for Linux)
    echo 3. Or download pre-built wheel from:
    echo    https://github.com/facebookresearch/detectron2/releases
    echo.
    echo For now, continuing with other dependencies...
    echo You can install detectron2 manually later.
    echo.
)
echo.

echo Step 3: Installing other dependencies...
pip install -r requirements_rcnn.txt
if %errorlevel% neq 0 (
    echo ERROR: Dependencies installation failed
    pause
    exit /b 1
)
echo.

echo ============================================================
echo Installation Complete!
echo ============================================================
echo.
echo Running installation test...
python test_installation.py
echo.
echo ============================================================
echo Ready to use!
echo Run: python main.py
echo ============================================================
pause
