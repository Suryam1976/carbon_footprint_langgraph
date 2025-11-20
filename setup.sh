#!/bin/bash
# Setup script for Carbon Footprint Analyzer (macOS/Linux)
# This script automates the setup process

set -e  # Exit on error

echo "======================================================================"
echo "  Carbon Footprint Analyzer - Automated Setup (macOS/Linux)"
echo "======================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.9 or higher"
    exit 1
fi

echo "[1/5] Python found"
python3 --version
echo ""

# Create virtual environment
echo "[2/5] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    echo "Virtual environment created successfully"
fi
echo ""

# Activate virtual environment and install dependencies
echo "[3/5] Installing dependencies..."
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo "Dependencies installed successfully"
echo ""

# Create .env file if it doesn't exist
echo "[4/5] Setting up environment file..."
if [ -f ".env" ]; then
    echo ".env file already exists. Skipping creation."
else
    cp .env.example .env
    echo ".env file created from template"
    echo ""
    echo "[IMPORTANT] Please edit .env file and add your ANTHROPIC_API_KEY"
    echo "Get your API key from: https://console.anthropic.com/"
fi
echo ""

# Run verification script
echo "[5/5] Verifying setup..."
python verify_setup.py
echo ""

echo "======================================================================"
echo "  Setup Complete!"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env file and add your ANTHROPIC_API_KEY"
echo "  2. Run: streamlit run streamlit_app.py"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source venv/bin/activate"
echo ""

