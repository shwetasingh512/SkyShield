# SkyShield One-Click Startup Script for Windows PowerShell
$Host.UI.RawUI.WindowTitle = "SkyShield - Aviation Safety Management System"

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "          SkyShield: Aviation Safety Management System" -ForegroundColor White
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $PSScriptRoot

Write-Host "[1/5] Checking virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment .venv..."
    python -m venv .venv
}

Write-Host "[2/5] Installing project dependencies..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "`n[3/5] Applying database migrations..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe manage.py migrate

Write-Host "`n[4/5] Seeding demonstration data..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe manage.py seed_demo_data

Write-Host "`n[5/5] Opening default web browser to http://127.0.0.1:8000/..." -ForegroundColor Green
Start-Process "http://127.0.0.1:8000/"

Write-Host "`n=====================================================================" -ForegroundColor Cyan
Write-Host "  SkyShield Server is now live at: http://127.0.0.1:8000/" -ForegroundColor Green
Write-Host "  Demo Accounts (Password for all is 'Password123!'):" -ForegroundColor White
Write-Host "    - Administrator:  admin" -ForegroundColor White
Write-Host "    - Safety Manager: safetymanager" -ForegroundColor White
Write-Host "    - Investigator:   investigator" -ForegroundColor White
Write-Host "    - Reporter:       reporter" -ForegroundColor White
Write-Host "  Press CTRL+C to stop the server." -ForegroundColor Yellow
Write-Host "=====================================================================`n" -ForegroundColor Cyan

& .\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
