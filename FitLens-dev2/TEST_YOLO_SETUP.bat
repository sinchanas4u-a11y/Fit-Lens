@echo off
echo ========================================
echo YOLOv8 + MediaPipe Setup Test
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist venv311\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv311\Scripts\activate.bat
    echo.
)

echo Running setup tests...
echo.

python test_yolo_setup.py

echo.
echo ========================================
pause
