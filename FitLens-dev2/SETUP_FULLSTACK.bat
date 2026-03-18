@echo off
echo ============================================================
echo Full-Stack Body Measurement System Setup
echo ============================================================
echo.

echo Step 1: Setting up Backend...
echo ============================================================
cd backend

echo Creating Python virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Backend setup complete!
echo.

cd ..

echo Step 2: Setting up Frontend...
echo ============================================================
cd frontend

echo Installing Node.js dependencies...
call npm install

echo.
echo Frontend setup complete!
echo.

cd ..

echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo To run the application:
echo.
echo 1. Start Backend (Terminal 1):
echo    cd backend
echo    venv\Scripts\activate
echo    python app.py
echo.
echo 2. Start Frontend (Terminal 2):
echo    cd frontend
echo    npm start
echo.
echo Or use: RUN_FULLSTACK.bat
echo.
pause
