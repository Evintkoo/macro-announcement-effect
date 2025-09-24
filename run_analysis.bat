@echo off
REM Windows Batch Script for Macro Announcement Effects Analysis
REM This script activates the virtual environment and runs the analysis

echo =========================================================
echo   MACRO ANNOUNCEMENT EFFECTS ANALYSIS - WINDOWS RUNNER
echo =========================================================

cd /d "%~dp0"

echo 📁 Working directory: %CD%

REM Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    echo ✅ Virtual environment found
    echo 🔄 Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  No virtual environment found in .venv
    echo 💡 Consider creating one with: python -m venv .venv
)

REM Check Python version
echo 🐍 Python version:
python --version

REM Check if requirements are installed
echo 📦 Checking if requirements are installed...
python -c "import pandas, numpy, yfinance" 2>nul && (
    echo ✅ Core packages available
) || (
    echo ⚠️  Some packages missing. Installing requirements...
    pip install -r requirements.txt
)

echo.
echo 🚀 Starting analysis...
echo.

REM Run the analysis
python run_analysis.py

echo.
echo 🏁 Script finished. Press any key to exit...
pause >nul