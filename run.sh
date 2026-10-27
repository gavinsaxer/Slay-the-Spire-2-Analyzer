#!/bin/bash
echo "=========================================="
echo "  Slay the Spire 2 Analyzer Setup"
echo "=========================================="

# Check if the virtual environment exists, if not, create it
if [ ! -d ".venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv .venv
else
    echo "[1/3] Virtual environment found."
fi

# Activate the environment and install dependencies
echo "[2/3] Activating environment and installing dependencies..."
source .venv/bin/activate
pip install -r requirements.txt --quiet

# Run the Streamlit dashboard
echo "[3/3] Launching dashboard..."
streamlit run dashboard.py