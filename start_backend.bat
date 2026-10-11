@echo off
title ReThread AI - Backend Server
echo ===================================================
echo   ReThread AI - Starting Backend API Server (FastAPI)
echo ===================================================
cd /d "%~dp0backend"
python run.py
pause
