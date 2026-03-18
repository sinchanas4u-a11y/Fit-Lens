@echo off
echo ========================================
echo Installing Backend Dependencies
echo ========================================
echo.

REM Activate virtual environment if exists
if exist ..\venv311\Scripts\activate.bat (
    echo Activating virtual environment...
    call ..\venv311\Scripts\activate.bat
    echo.
)

echo Installing Flask and related packages...
pip install flask>=2.3.0
pip install flask-cors>=4.0.0

echo.
echo Installing computer vision packages...
pip install opencv-python>=4.8.0
pip install mediapipe>=0.10.0
pip install numpy>=1.24.0
pip install Pillow>=10.0.0

echo.
echo Installing YOLOv8...
pip install ultralytics>=8.0.0

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo You can now run:
echo   python app_updated.py
echo.
pause
