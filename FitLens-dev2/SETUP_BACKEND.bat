@echo off
echo ========================================
echo Backend Setup - Installing Dependencies
echo ========================================
echo.

REM Activate virtual environment
if exist venv311\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv311\Scripts\activate.bat
    echo.
)

echo Installing backend dependencies...
echo This may take a few minutes...
echo.

REM Navigate to backend
cd backend

REM Install Flask and related
echo [1/9] Installing Flask...
pip install flask>=2.3.0

echo [2/9] Installing Flask-CORS...
pip install flask-cors>=4.0.0

echo [3/9] Installing Flask-SocketIO...
pip install flask-socketio>=5.3.0

echo [4/9] Installing Python-SocketIO...
pip install python-socketio>=5.9.0

echo [5/9] Installing OpenCV...
pip install opencv-python>=4.8.0

echo [6/9] Installing MediaPipe...
pip install mediapipe>=0.10.0

echo [7/9] Installing NumPy...
pip install numpy>=1.24.0

echo [8/9] Installing Pillow...
pip install Pillow>=10.0.0

echo [9/9] Installing Ultralytics (YOLOv8)...
pip install ultralytics>=8.0.0

echo.
echo ========================================
echo Backend Setup Complete!
echo ========================================
echo.
echo To start the backend server, run:
echo   cd backend
echo   python app.py
echo.
echo Or use: START_BACKEND.bat
echo.
pause
