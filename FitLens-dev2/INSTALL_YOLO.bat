@echo off
echo ========================================
echo YOLOv8 + MediaPipe Installation
echo ========================================
echo.

REM Check if virtual environment exists
if exist venv311\Scripts\activate.bat (
    echo Activating existing virtual environment...
    call venv311\Scripts\activate.bat
) else (
    echo No virtual environment found.
    echo Please create one first or install globally.
    echo.
    set /p CONTINUE="Continue with global installation? (y/n): "
    if /i not "%CONTINUE%"=="y" (
        echo Installation cancelled.
        pause
        exit /b 1
    )
)

echo.
echo Installing YOLOv8 and dependencies...
echo This may take a few minutes...
echo.

REM Upgrade pip
python -m pip install --upgrade pip

REM Install core dependencies
echo Installing core packages...
pip install opencv-python>=4.8.0
pip install mediapipe>=0.10.0
pip install numpy>=1.24.0
pip install Pillow>=10.0.0

REM Install YOLOv8
echo.
echo Installing YOLOv8 (ultralytics)...
pip install ultralytics>=8.0.0

REM Install backend dependencies (optional)
echo.
set /p INSTALL_BACKEND="Install backend dependencies (Flask, etc.)? (y/n): "
if /i "%INSTALL_BACKEND%"=="y" (
    echo Installing backend dependencies...
    pip install flask>=2.3.0
    pip install flask-cors>=4.0.0
    pip install flask-socketio>=5.3.0
    pip install python-socketio>=5.9.0
    pip install torch>=2.0.0
    pip install torchvision>=0.15.0
    pip install scipy>=1.11.0
    pip install scikit-image>=0.21.0
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.

REM Test installation
echo Testing installation...
echo.
python test_yolo_setup.py

echo.
echo ========================================
echo Next Steps:
echo ========================================
echo.
echo 1. Process your first image:
echo    python process_images_yolo.py image.jpg
echo.
echo 2. Process multiple images:
echo    python process_images_yolo.py img1.jpg img2.jpg img3.jpg
echo.
echo 3. With height calibration:
echo    python process_images_yolo.py image.jpg --reference-size 170
echo.
echo 4. See QUICKSTART_YOLO.md for more examples
echo.
echo ========================================
pause
