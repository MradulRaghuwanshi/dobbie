@echo off
REM Dobbie Startup Script - Desktop Version
REM This runs Dobbie as a desktop application

cd /d c:\Users\mradu\Desktop\dobbie

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Run Dobbie desktop application
python main.py

exit /b 0
