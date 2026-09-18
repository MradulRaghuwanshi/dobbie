#!/usr/bin/env powershell
# Quick Start Script for Dobbie
# This script helps set up Dobbie with all required dependencies

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  DOBBIE - Magical Desktop Assistant Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
python --version | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Python is installed" -ForegroundColor Green
} else {
    Write-Host "✗ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "  Please install Python 3.9+ from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
python -m pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Check for config.json
Write-Host ""
Write-Host "Checking configuration..." -ForegroundColor Yellow
if (Test-Path "config.json") {
    Write-Host "✓ config.json found" -ForegroundColor Green
} else {
    Write-Host "✗ config.json not found" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Edit config.json and add your Gmail credentials:" -ForegroundColor White
Write-Host "     - Get 'App Passwords' from https://myaccount.google.com/security" -ForegroundColor Gray
Write-Host "     - Enable 2-Factor Authentication first" -ForegroundColor Gray
Write-Host "  2. Run: python app.py" -ForegroundColor White
Write-Host "  3. Open http://localhost:5000 in your browser" -ForegroundColor White
Write-Host ""
Write-Host "For detailed setup instructions, see SETUP.md" -ForegroundColor Cyan
Write-Host ""
