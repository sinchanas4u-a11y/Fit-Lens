@echo off
echo ============================================================
echo Body Measurement Application Launcher
echo ============================================================
echo.

REM Check if venv311 exists
if exist venv311\Scripts\activate.bat (
    echo Activating Python 3.11 virtual environment...
    call venv311\Scripts\activate.bat
    echo.
    echo Virtual environment activated!
    echo Python version:
    python --version
    echo.
    
    REM Check if dependencies are installed
    echo Checking dependencies...
    python -c "import cv2; print('✓ OpenCV installed')" 2>nul
    if %errorlevel% neq 0 (
        echo.
        echo Installing dependencies...
        pip install opencv-python numpy scipy pillow albumentations tqdm pyyaml
    )
    echo.
    
    REM Run the application
    echo Starting application...
    echo.
    python pose_capture.py
    
) else (
    echo ERROR: Virtual environment not found!
    echo.
    echo Please create it first:
    echo   py -3.11 -m venv venv311
    echo   venv311\Scripts\activate
    echo   pip install opencv-python mediapipe numpy
    echo.
    pause
)
