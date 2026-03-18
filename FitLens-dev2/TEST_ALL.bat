@echo off
REM Test FitLens Dependencies and Application

echo ============================================================
echo FitLens - Dependency and Application Test
echo ============================================================
echo.

REM Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

echo.
echo [1/2] Testing Dependencies...
echo ============================================================
python test_dependencies.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Dependency test failed!
    pause
    exit /b 1
)

echo.
echo.
echo [2/2] Testing Application Modules...
echo ============================================================
python test_application.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Application test failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo All Tests Passed!
echo ============================================================
echo.
echo Your FitLens application is ready to use.
echo.
echo Quick Start Options:
echo   1. RUN_MEDIAPIPE.bat   - Run pose capture
echo   2. RUN_DASHBOARD.bat   - Run web dashboard
echo   3. RUN_FULLSTACK.bat   - Run full application
echo.
pause
