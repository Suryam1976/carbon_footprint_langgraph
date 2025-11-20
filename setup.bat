@echo off
REM Setup script for Carbon Footprint Analyzer (Windows)
REM This script automates the setup process

echo ======================================================================
echo   Carbon Footprint Analyzer - Automated Setup (Windows)
echo ======================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Python found
python --version
echo.

REM Create virtual environment
echo [2/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Skipping creation.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)
echo.

REM Activate virtual environment and install dependencies
echo [3/5] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

REM Create .env file if it doesn't exist
echo [4/5] Setting up environment file...
if exist .env (
    echo .env file already exists. Skipping creation.
) else (
    copy .env.example .env
    echo .env file created from template
    echo.
    echo [IMPORTANT] Please edit .env file and add your ANTHROPIC_API_KEY
    echo Get your API key from: https://console.anthropic.com/
)
echo.

REM Run verification script
echo [5/5] Verifying setup...
python verify_setup.py
echo.

echo ======================================================================
echo   Setup Complete!
echo ======================================================================
echo.
echo Next steps:
echo   1. Edit .env file and add your ANTHROPIC_API_KEY
echo   2. Run: streamlit run streamlit_app.py
echo.
echo To activate the virtual environment in the future, run:
echo   venv\Scripts\activate.bat
echo.
pause

