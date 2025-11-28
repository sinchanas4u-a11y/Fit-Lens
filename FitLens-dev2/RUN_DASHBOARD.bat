@echo off
echo ============================================================
echo Body Measurement Dashboard - Advanced Version
echo ============================================================
echo.

REM Check for venv311
if exist venv311\Scripts\activate.bat (
    echo Activating Python 3.11 virtual environment...
    call venv311\Scripts\activate.bat
) else (
    echo Using global Python
)

echo.
echo Python version:
python --version
echo.

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

python -c "import customtkinter" 2>nul
if %errorlevel% neq 0 (
    echo Installing customtkinter...
    pip install customtkinter
)

python -c "import pyttsx3" 2>nul
if %errorlevel% neq 0 (
    echo Installing pyttsx3...
    pip install pyttsx3
)

python -c "import torch" 2>nul
if %errorlevel% neq 0 (
    echo Installing PyTorch...
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
)

echo.
echo ============================================================
echo Starting Dashboard Application...
echo ============================================================
echo.

python dashboard_app.py

if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo Error occurred!
    echo ============================================================
    pause
)
