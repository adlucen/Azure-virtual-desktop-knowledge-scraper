@echo off
REM Setup script for AVD Knowledge Scraper on Windows

echo ==========================================
echo AVD Knowledge Scraper - Setup (Windows)
echo ==========================================
echo.

REM Check Python
echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Install from python.org
    pause
    exit /b 1
)
python --version
echo.

REM Create venv
echo [2/4] Creating virtual environment...
if exist venv (
    echo Virtual environment exists, skipping...
) else (
    python -m venv venv
    echo Created
)
echo.

REM Activate and install
echo [3/4] Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo Installed
echo.

REM Create directories
echo [4/4] Creating directories...
if not exist output\microsoft_docs mkdir output\microsoft_docs
if not exist output\azure_updates mkdir output\azure_updates
if not exist output\blogs mkdir output\blogs
if not exist logs mkdir logs
echo Done
echo.

echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo   1. Activate: venv\Scripts\activate
echo   2. Run: python main.py --mode once
echo.
echo Optional - Reddit API (for Reddit scraping):
echo   set REDDIT_CLIENT_ID=your_id
echo   set REDDIT_CLIENT_SECRET=your_secret
echo.
pause
