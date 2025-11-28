@echo off
echo ============================================================
echo Starting Backend Server with Diagnostics
echo ============================================================
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo.
echo Testing camera...
python test_camera.py
echo.

echo.
echo Starting Flask server...
echo Backend will run on: http://localhost:5000
echo.
echo Press Ctrl+C to stop
echo.

python app.py

pause
