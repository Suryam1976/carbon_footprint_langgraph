@echo off
REM Quick run script for Carbon Footprint Analyzer (Windows)

echo ======================================================================
echo   Carbon Footprint Analyzer - Starting Application
echo ======================================================================
echo.

REM Check if virtual environment exists
if not exist venv (
    echo [ERROR] Virtual environment not found!
    echo Please run setup.bat first to set up the project.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found!
    echo Please copy .env.example to .env and add your API key.
    pause
    exit /b 1
)

echo Starting Streamlit application...
echo.
echo The application will open in your browser at http://localhost:8501
echo Press Ctrl+C to stop the server
echo.

streamlit run streamlit_app.py

