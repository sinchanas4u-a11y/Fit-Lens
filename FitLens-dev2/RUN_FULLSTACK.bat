@echo off
echo ============================================================
echo Starting Full-Stack Body Measurement System
echo ============================================================
echo.

echo Starting Backend Server...
start cmd /k "cd backend && venv\Scripts\activate && python app.py"

timeout /t 3 /nobreak > nul

echo Starting Frontend Server...
start cmd /k "cd frontend && npm start"

echo.
echo ============================================================
echo Both servers are starting...
echo ============================================================
echo.
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Press any key to stop both servers...
pause > nul

echo Stopping servers...
taskkill /FI "WINDOWTITLE eq *backend*" /F
taskkill /FI "WINDOWTITLE eq *frontend*" /F
