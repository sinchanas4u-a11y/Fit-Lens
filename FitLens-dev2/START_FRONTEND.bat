@echo off
echo ========================================
echo Starting Frontend Server
echo ========================================
echo.

echo Setting environment variables...
set SKIP_PREFLIGHT_CHECK=true
set DANGEROUSLY_DISABLE_HOST_CHECK=true

echo.
echo Starting React development server...
echo Server will run on: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo.
echo ========================================
echo.

cd frontend
npm start
