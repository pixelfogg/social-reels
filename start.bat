@echo off
setlocal enabledelayedexpansion
title ReelsAI Studio - YouTube to Viral Shorts & Reels

echo =================================================================
echo   [ReelsAI Studio] Automated YouTube to Viral Shorts & Reels
echo =================================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please download and install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

:: Check and create virtual environment if not present
if not exist ".venv\Scripts\python.exe" (
    echo [*] Setting up virtual environment (.venv)...
    python -m venv .venv
    echo [*] Upgrading pip...
    .\.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
    echo [*] Installing all required AI video dependencies from requirements.txt...
    echo [*] This will take about 1-2 minutes on first run...
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo [*] Dependencies installed successfully!
    echo.
)

:: Launch Studio
echo [*] Launching ReelsAI Studio Server...
echo [*] Opening browser at http://localhost:8000 ...
start http://localhost:8000

.\.venv\Scripts\python.exe run_studio.py

pause
