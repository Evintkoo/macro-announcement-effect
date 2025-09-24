# PowerShell Script for Macro Announcement Effects Analysis
# This script activates the virtual environment and runs the analysis

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  MACRO ANNOUNCEMENT EFFECTS ANALYSIS - POWERSHELL RUNNER" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# Change to script directory
Set-Location $PSScriptRoot

Write-Host "📁 Working directory: $(Get-Location)" -ForegroundColor Green

# Check if virtual environment exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "✅ Virtual environment found" -ForegroundColor Green
    Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
    & .venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠️  No virtual environment found in .venv" -ForegroundColor Yellow
    Write-Host "💡 Consider creating one with: python -m venv .venv" -ForegroundColor Blue
}

# Check Python version
Write-Host "🐍 Python version:" -ForegroundColor Blue
python --version

# Check if requirements are installed
Write-Host "📦 Checking if requirements are installed..." -ForegroundColor Blue
try {
    python -c "import pandas, numpy, yfinance" 2>$null
    Write-Host "✅ Core packages available" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Some packages missing. Installing requirements..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

Write-Host ""
Write-Host "🚀 Starting analysis..." -ForegroundColor Green
Write-Host ""

# Run the analysis
python run_analysis.py

Write-Host ""
Write-Host "🏁 Script finished. Press any key to exit..." -ForegroundColor Green
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")