#!/usr/bin/env bash
set -e

echo "================================================================="
echo "  [ReelsAI Studio] Automated YouTube to Viral Shorts & Reels"
echo "================================================================="
echo ""

# Check python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 is not installed. Please install Python 3.10+."
    exit 1
fi

# Setup venv if missing
if [ ! -f ".venv/bin/python" ]; then
    echo "[*] Setting up virtual environment (.venv)..."
    python3 -m venv .venv
    ./.venv/bin/pip install --upgrade pip --quiet
    echo "[*] Installing required AI video dependencies from requirements.txt..."
    ./.venv/bin/pip install -r requirements.txt
    echo "[*] Dependencies installed successfully!"
    echo ""
fi

# Launch
echo "[*] Starting ReelsAI Studio on http://localhost:8000 ..."
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8000 &
elif command -v open &> /dev/null; then
    open http://localhost:8000 &
fi

./.venv/bin/python run_studio.py
