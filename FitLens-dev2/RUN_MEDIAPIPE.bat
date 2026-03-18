@echo off
echo ============================================================
echo MediaPipe Pose Capture - Quick Launcher
echo ============================================================
echo.

REM Check if running in venv
python -c "import sys; exit(0 if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 1)" 2>nul

if %errorlevel% equ 0 (
    echo Running in virtual environment
) else (
    echo Checking for venv311...
    if exist venv311\Scripts\activate.bat (
        echo Activating venv311...
        call venv311\Scripts\activate.bat
    ) else (
        echo Using global Python
    )
)

echo.
echo Python version:
python --version
echo.

REM Check and install dependencies
echo Checking dependencies...
python -c "import cv2" 2>nul
if %errorlevel% neq 0 (
    echo Installing opencv-python...
    pip install opencv-python
)

python -c "import mediapipe" 2>nul
if %errorlevel% neq 0 (
    echo Installing mediapipe...
    pip install mediapipe
)

python -c "import numpy" 2>nul
if %errorlevel% neq 0 (
    echo Installing numpy...
    pip install numpy
)

echo.
echo ============================================================
echo Starting MediaPipe Pose Capture...
echo ============================================================
echo.
echo Instructions:
echo 1. Stand in front of camera
echo 2. Align with the outline
echo 3. Hold pose for 3 seconds when GREEN
echo 4. Press 'Q' to quit
echo.

python pose_capture.py

echo.
echo ============================================================
echo Application closed
echo ============================================================
pause
