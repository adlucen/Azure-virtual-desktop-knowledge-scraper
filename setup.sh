#!/bin/bash
# Setup script for AVD Knowledge Scraper on Linux/macOS

set -e

echo "=========================================="
echo "AVD Knowledge Scraper - Setup"
echo "=========================================="
echo ""

# Check Python
echo "[1/4] Checking Python..."
python3 --version
echo ""

# Create venv
echo "[2/4] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment exists, skipping..."
else
    python3 -m venv venv
    echo "Created"
fi
echo ""

# Activate and install
echo "[3/4] Installing dependencies..."
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "Installed"
echo ""

# Create directories
echo "[4/4] Creating directories..."
mkdir -p output/{microsoft_docs,azure_updates,blogs}
mkdir -p logs
echo "Done"
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Activate: source venv/bin/activate"
echo "  2. Run: python main.py --mode once"
echo ""
echo "Optional - Reddit API (for Reddit scraping):"
echo "  export REDDIT_CLIENT_ID=your_id"
echo "  export REDDIT_CLIENT_SECRET=your_secret"
echo ""
