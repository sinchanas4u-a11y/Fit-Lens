@echo off
echo ========================================
echo Setup Vite Frontend
echo ========================================
echo.

echo Step 1: Navigate to frontend-vite folder
cd frontend-vite

echo.
echo Step 2: Installing dependencies...
echo This may take a few minutes...
call npm install

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the development server:
echo   cd frontend-vite
echo   npm run dev
echo.
echo The app will open at: http://localhost:3000
echo.
echo To build for production:
echo   npm run build
echo.
pause
