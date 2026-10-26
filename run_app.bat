@echo off
title SkyShield - Aviation Safety Management System
echo =====================================================================
echo           SkyShield: Aviation Safety Management System
echo =====================================================================
echo.

cd /d "%~dp0"

echo [1/5] Checking virtual environment...
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment .venv...
    python -m venv .venv
)

echo [2/5] Activating virtual environment and installing dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo [3/5] Applying database migrations...
python manage.py migrate

echo.
echo [4/5] Seeding demonstration dataset...
python manage.py seed_demo_data

echo.
echo [5/5] Launching default web browser to http://127.0.0.1:8000/...
timeout /t 2 /nobreak >nul
start http://127.0.0.1:8000/

echo.
echo =====================================================================
echo   SkyShield Server is now live at: http://127.0.0.1:8000/
echo   Demo Accounts (Password for all is 'Password123!'):
echo     - Administrator:  admin
echo     - Safety Manager: safetymanager
echo     - Investigator:   investigator
echo     - Reporter:       reporter
echo   Press CTRL+C in this terminal window to stop the server.
echo =====================================================================
echo.

python manage.py runserver 127.0.0.1:8000
pause
