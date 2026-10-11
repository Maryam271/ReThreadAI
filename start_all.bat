@echo off
title ReThread AI Launcher
echo ===================================================
echo   Launching ReThread AI MVP (Backend + Frontend)
echo ===================================================
echo Starting FastAPI Backend in separate window...
start "ReThread AI Backend" "%~dp0start_backend.bat"

echo Waiting 2 seconds for backend initialization...
timeout /t 2 /nobreak >nul

echo Starting Vite Frontend in separate window...
start "ReThread AI Frontend" "%~dp0start_frontend.bat"

echo.
echo Application launched!
echo Access the Studio at: http://localhost:5173
echo Backend Health API:   http://localhost:8000/api/health
echo ===================================================
timeout /t 5
