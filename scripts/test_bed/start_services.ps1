# PowerShell script to start all SentinelVNC services for testing
# Run this script to start all required services

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "SentinelVNC Test Environment Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠ Node.js not found (needed for proxy)" -ForegroundColor Yellow
}

# Install Python dependencies
Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$requirementsFile = Join-Path $scriptDir "requirements.txt"
if (Test-Path $requirementsFile) {
    pip install -r $requirementsFile
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "⚠ requirements.txt not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Services to Start" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Start these services in separate PowerShell windows:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Risk Engine (port 9000):" -ForegroundColor Cyan
Write-Host "   cd risk_engine" -ForegroundColor White
Write-Host "   uvicorn main:app --host 0.0.0.0 --port 9000" -ForegroundColor White
Write-Host ""
Write-Host "2. Response Engine (port 9200):" -ForegroundColor Cyan
Write-Host "   cd response_engine" -ForegroundColor White
Write-Host "   uvicorn main:app --host 0.0.0.0 --port 9200" -ForegroundColor White
Write-Host ""
Write-Host "3. Forensics Service (port 9100):" -ForegroundColor Cyan
Write-Host "   cd forensics" -ForegroundColor White
Write-Host "   uvicorn main:app --host 0.0.0.0 --port 9100" -ForegroundColor White
Write-Host ""
Write-Host "4. Blockchain Gateway (port 8080):" -ForegroundColor Cyan
Write-Host "   python -m uvicorn blockchain.gateway:app --host 0.0.0.0 --port 8080" -ForegroundColor White
Write-Host ""
Write-Host "5. Proxy (port 5900):" -ForegroundColor Cyan
Write-Host "   cd proxy" -ForegroundColor White
Write-Host "   node index.js" -ForegroundColor White
Write-Host ""
Write-Host "After starting services, run tests with:" -ForegroundColor Yellow
Write-Host "   python scripts/test_bed/attack_scripts/clipboard_exfil.py" -ForegroundColor White
Write-Host ""


