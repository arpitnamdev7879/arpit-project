@echo off
title TalentGPT Startup
color 0A
echo.
echo  ========================================
echo   TalentGPT - AI Talent Acquisition
echo  ========================================
echo.

REM Check if .env exists
if not exist "backend\.env" (
    echo  [SETUP] Creating .env from template...
    copy backend\.env.example backend\.env > nul
    echo  [ACTION REQUIRED] Open backend\.env and add your API keys!
    echo.
    notepad backend\.env
    pause
)

REM Install Python dependencies
echo  [1/3] Installing Python dependencies...
cd backend
pip install -r requirements.txt -q
if errorlevel 1 (
    echo  [ERROR] pip install failed. Make sure Python is installed.
    pause
    exit /b 1
)

echo  [2/3] Starting TalentGPT API server...
echo  API will be available at: http://localhost:8000
echo  API Docs at: http://localhost:8000/docs
echo.
start "TalentGPT API" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo  [3/3] Opening Dashboard...
timeout /t 3 /nobreak > nul
cd ..\frontend
start "" index.html

echo.
echo  ========================================
echo   TalentGPT is running!
echo   Dashboard: frontend\index.html
echo   API Docs:  http://localhost:8000/docs
echo  ========================================
echo.
pause
