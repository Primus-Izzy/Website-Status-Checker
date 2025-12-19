@echo off
REM Quick start script for Website Status Checker Web GUI (Windows)

echo ============================================================
echo Website Status Checker - Web GUI Quick Start
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Run the Python quick start script
python start_gui.py

pause
