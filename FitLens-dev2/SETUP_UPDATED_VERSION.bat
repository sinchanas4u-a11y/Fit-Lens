@echo off
echo ========================================
echo Setup Updated Workflow Version
echo ========================================
echo.

echo This will:
echo   1. Backup current backend/app.py
echo   2. Use the updated backend (app_updated.py)
echo   3. Show you how to update the frontend
echo.

set /p CONTINUE="Continue? (y/n): "
if /i not "%CONTINUE%"=="y" (
    echo Setup cancelled.
    pause
    exit /b 0
)

echo.
echo Step 1: Backing up current backend...
if exist backend\app.py (
    copy backend\app.py backend\app_backup.py
    echo   ✓ Backed up to backend\app_backup.py
) else (
    echo   ! No existing app.py found
)

echo.
echo Step 2: Using updated backend...
copy backend\app_updated.py backend\app.py
echo   ✓ Updated backend\app.py

echo.
echo Step 3: Frontend update instructions
echo.
echo To use the updated frontend component:
echo.
echo   1. Open: frontend\src\App.js
echo.
echo   2. Add this import at the top:
echo      import UploadModeUpdated from './components/UploadModeUpdated';
echo.
echo   3. Replace UploadMode with UploadModeUpdated in your component
echo.
echo   4. Save the file
echo.

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Start backend:  cd backend ^&^& python app.py
echo   2. Start frontend: cd frontend ^&^& npm start
echo   3. Open browser:   http://localhost:3000
echo.
echo See UPDATED_WORKFLOW_GUIDE.md for complete instructions
echo.
pause
