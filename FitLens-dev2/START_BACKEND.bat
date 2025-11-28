@echo off
echo ========================================
echo Starting Backend Server
echo ========================================
echo.

REM Activate virtual environment
if exist venv311\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv311\Scripts\activate.bat
    echo.
)

echo Starting Flask backend server...
echo Server will run on: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.
echo ========================================
echo.

cd backend
python app.py
