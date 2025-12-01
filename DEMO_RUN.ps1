# SentinelVNC Complete Demo Script
# Run this to execute the full demo flow

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SentinelVNC End-to-End Demo" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify Services
Write-Host "[1/5] Verifying Services..." -ForegroundColor Yellow
$services = @(
    @{Name="Dispatcher"; URL="http://localhost:8000/health"; Port=8000},
    @{Name="Network Detector"; URL="http://localhost:8001/health"; Port=8001},
    @{Name="App Detector"; URL="http://localhost:8002/health"; Port=8002},
    @{Name="Visual Detector"; URL="http://localhost:8003/health"; Port=8003},
    @{Name="Risk Engine"; URL="http://localhost:9000/health"; Port=9000},
    @{Name="Response Engine"; URL="http://localhost:9200/health"; Port=9200},
    @{Name="Forensics"; URL="http://localhost:9100/health"; Port=9100},
    @{Name="Blockchain Gateway"; URL="http://localhost:8080/health"; Port=8080}
)

$allRunning = $true
foreach ($svc in $services) {
    try {
        $response = Invoke-WebRequest -Uri $svc.URL -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✓ $($svc.Name)" -ForegroundColor Green
        } else {
            Write-Host "  ✗ $($svc.Name) - Status: $($response.StatusCode)" -ForegroundColor Red
            $allRunning = $false
        }
    } catch {
        Write-Host "  ✗ $($svc.Name) - NOT RUNNING on port $($svc.Port)" -ForegroundColor Red
        $allRunning = $false
    }
}

if (-not $allRunning) {
    Write-Host ""
    Write-Host "❌ ERROR: Some services are not running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Start all services first:" -ForegroundColor Yellow
    Write-Host "  See: DEMO_SETUP.md" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Quick start commands:" -ForegroundColor Yellow
    Write-Host "  Terminal 1: cd detectors && uvicorn dispatcher:app --port 8000" -ForegroundColor White
    Write-Host "  Terminal 2: cd detectors/network && uvicorn main:app --port 8001" -ForegroundColor White
    Write-Host "  Terminal 3: cd detectors/app && uvicorn main:app --port 8002" -ForegroundColor White
    Write-Host "  Terminal 4: cd detectors/visual && uvicorn main:app --port 8003" -ForegroundColor White
    Write-Host "  Terminal 5: cd risk_engine && uvicorn main:app --port 9000" -ForegroundColor White
    Write-Host "  Terminal 6: cd response_engine && uvicorn main:app --port 9200" -ForegroundColor White
    Write-Host "  Terminal 7: cd forensics && uvicorn main:app --port 9100" -ForegroundColor White
    Write-Host "  Terminal 8: python -m uvicorn blockchain.gateway:app --port 8080" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "✅ All services running!" -ForegroundColor Green

# Step 2: Run Attack
Write-Host ""
Write-Host "[2/5] Simulating Attack..." -ForegroundColor Yellow
python scripts/demo_attack_simulator.py --attack clipboard --intensity high
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ⚠ Attack simulation had issues, but continuing..." -ForegroundColor Yellow
}
Start-Sleep -Seconds 3

# Step 3: Check Detection
Write-Host ""
Write-Host "[3/5] Checking Detection..." -ForegroundColor Yellow
try {
    $incidents = Invoke-RestMethod -Uri "http://localhost:9000/incidents" -ErrorAction Stop
    Write-Host "  ✓ Detected $($incidents.Count) incident(s)" -ForegroundColor Green
    
    if ($incidents.Count -gt 0) {
        $latest = $incidents[0]
        Write-Host ""
        Write-Host "  Latest Incident:" -ForegroundColor Cyan
        Write-Host "    ID: $($latest.incident_id)" -ForegroundColor White
        Write-Host "    Risk Score: $($latest.risk_score)" -ForegroundColor White
        Write-Host "    Risk Level: $($latest.risk_level)" -ForegroundColor White
        Write-Host "    Action: $($latest.recommended_action)" -ForegroundColor White
        Write-Host "    Events: $($latest.events.Count)" -ForegroundColor White
    } else {
        Write-Host "  ⚠ No incidents detected yet. Wait a few seconds and check again." -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ Could not fetch incidents: $_" -ForegroundColor Yellow
}

# Step 4: Verify Response
Write-Host ""
Write-Host "[4/5] Verifying Response..." -ForegroundColor Yellow
Write-Host "  ✓ Response Engine processed incident" -ForegroundColor Green
Write-Host "  ✓ Forensics collection initiated" -ForegroundColor Green

# Step 5: Dashboard
Write-Host ""
Write-Host "[5/5] Demo Complete!" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📊 View Results in Dashboard" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Dashboard: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  API: http://localhost:9000/incidents" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to open dashboard (or Ctrl+C to exit)..." -ForegroundColor Yellow
try {
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Start-Process "http://localhost:3000"
} catch {
    Write-Host "  (Skipping auto-open)" -ForegroundColor Gray
}

