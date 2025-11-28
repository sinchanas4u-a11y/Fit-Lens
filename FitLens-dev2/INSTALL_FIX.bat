@echo off
echo ========================================
echo Installing with Network Timeout Fix
echo ========================================
echo.

REM Activate virtual environment
if exist venv311\Scripts\activate.bat (
    call venv311\Scripts\activate.bat
)

echo Step 1: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Step 2: Installing core packages...
pip install --timeout=1000 --retries 10 numpy opencv-python pillow

echo.
echo Step 3: Installing MediaPipe...
pip install --timeout=1000 --retries 10 mediapipe

echo.
echo Step 4: Installing PyTorch (CPU version)...
pip install --timeout=1000 torch torchvision --index-url https://download.pytorch.org/whl/cpu

echo.
echo Step 5: Installing ultralytics (YOLOv8)...
pip install --timeout=1000 --retries 10 ultralytics

echo.
echo Step 6: Testing installation...
python test_yolo_setup.py

echo.
echo ========================================
echo Installation Complete!
echo ========================================
pause
