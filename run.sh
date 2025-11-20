#!/bin/bash
# Quick run script for Carbon Footprint Analyzer (macOS/Linux)

echo "======================================================================"
echo "  Carbon Footprint Analyzer - Starting Application"
echo "======================================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found!"
    echo "Please run ./setup.sh first to set up the project."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "[WARNING] .env file not found!"
    echo "Please copy .env.example to .env and add your API key."
    exit 1
fi

echo "Starting Streamlit application..."
echo ""
echo "The application will open in your browser at http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run streamlit_app.py

