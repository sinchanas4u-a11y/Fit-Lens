@echo off
echo ============================================================
echo Body Measurement System - Diagnostics
echo ============================================================
echo.

echo Step 1: Testing Camera Hardware
echo ============================================================
cd backend
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
python test_camera.py
echo.

echo Step 2: Checking Backend Health
echo ============================================================
echo Testing if backend is running...
curl -s http://localhost:5000/api/health
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Backend is not running!
    echo Please start backend first:
    echo   cd backend
    echo   python app.py
) else (
    echo.
    echo Backend is running!
)
echo.

echo Step 3: Testing Camera Start Endpoint
echo ============================================================
curl -X POST http://localhost:5000/api/camera/start
echo.
echo.

echo Step 4: Checking Python Packages
echo ============================================================
echo Checking required packages...
python -c "import cv2; print('✓ opencv-python')" 2>nul || echo "✗ opencv-python MISSING"
python -c "import mediapipe; print('✓ mediapipe')" 2>nul || echo "✗ mediapipe MISSING"
python -c "import flask; print('✓ flask')" 2>nul || echo "✗ flask MISSING"
python -c "import flask_socketio; print('✓ flask-socketio')" 2>nul || echo "✗ flask-socketio MISSING"
echo.

echo Step 5: Checking Ports
echo ============================================================
echo Checking if ports are in use...
netstat -an | findstr ":5000" >nul
if %errorlevel% equ 0 (
    echo ✓ Port 5000 is in use (Backend should be running)
) else (
    echo ✗ Port 5000 is NOT in use (Backend not running)
)

netstat -an | findstr ":3000" >nul
if %errorlevel% equ 0 (
    echo ✓ Port 3000 is in use (Frontend should be running)
) else (
    echo ✗ Port 3000 is NOT in use (Frontend not running)
)
echo.

echo ============================================================
echo Diagnostics Complete
echo ============================================================
echo.
echo If camera test passed but frontend shows blank:
echo 1. Ensure backend is running (python app.py)
echo 2. Ensure frontend is running (npm start)
echo 3. Check browser console for errors (F12)
echo 4. Allow camera permissions in browser
echo.
echo See TROUBLESHOOT_CAMERA.md for detailed help
echo.
pause
