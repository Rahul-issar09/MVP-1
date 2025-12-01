# SentinelVNC Demo Setup Guide

## Quick Start (4 Steps)

### Step 1: Start All Services (8 terminals)

**Terminal 1 - Dispatcher:**
```powershell
cd detectors
uvicorn dispatcher:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Network Detector:**
```powershell
cd detectors/network
uvicorn main:app --host 0.0.0.0 --port 8001
```

**Terminal 3 - App Detector:**
```powershell
cd detectors/app
uvicorn main:app --host 0.0.0.0 --port 8002
```

**Terminal 4 - Visual Detector:**
```powershell
cd detectors/visual
uvicorn main:app --host 0.0.0.0 --port 8003
```

**Terminal 5 - Risk Engine:**
```powershell
cd risk_engine
uvicorn main:app --host 0.0.0.0 --port 9000
```

**Terminal 6 - Response Engine:**
```powershell
cd response_engine
uvicorn main:app --host 0.0.0.0 --port 9200
```

**Terminal 7 - Forensics:**
```powershell
cd forensics
uvicorn main:app --host 0.0.0.0 --port 9100
```

**Terminal 8 - Blockchain Gateway:**
```powershell
python -m uvicorn blockchain.gateway:app --host 0.0.0.0 --port 8080
```

**Terminal 9 - Dashboard (Optional, for viewing):**
```powershell
cd dashboard
npm run dev
```

### Step 2: Configure Proxy (Optional - for real VNC)

If you want to test with actual VNC traffic:

```powershell
cd proxy
$env:DETECTOR_ENDPOINT="http://localhost:8000/events"
$env:PROXY_LISTEN_PORT="5900"
$env:UPSTREAM_HOST="127.0.0.1"
$env:UPSTREAM_PORT="5901"
$env:PROXY_ADMIN_PORT="8000"
node index.js
```

### Step 3: Run Demo

```powershell
.\DEMO_RUN.ps1
```

Or manually run the attack simulator:

```powershell
python scripts/demo_attack_simulator.py --attack clipboard --intensity high
```

### Step 4: View Dashboard

Open: http://localhost:3000

## Demo Flow

1. **Attack** → Simulator sends events to dispatcher
2. **Detection** → Detectors analyze and send to Risk Engine
3. **Risk Scoring** → Risk Engine creates incident
4. **Response** → Response Engine takes action (kill/deceive/allow)
5. **Forensics** → Artifacts collected
6. **Dashboard** → View all data in real-time

## Attack Types

You can simulate different attack types:

```powershell
# Clipboard exfiltration (triggers app detector)
python scripts/demo_attack_simulator.py --attack clipboard --intensity high

# File transfer (triggers network detector)
python scripts/demo_attack_simulator.py --attack file --intensity high

# DNS tunneling (triggers network detector)
python scripts/demo_attack_simulator.py --attack dns --intensity high

# Screenshot burst (triggers visual detector)
python scripts/demo_attack_simulator.py --attack screenshot --intensity high

# All attacks
python scripts/demo_attack_simulator.py --attack all --intensity high
```

## Troubleshooting

### Services Not Starting

**Error: `uvicorn: command not found`**
```powershell
pip install uvicorn fastapi
```

**Error: `Module not found`**
```powershell
# Install project dependencies
pip install -r detectors/requirements.txt
pip install -r risk_engine/requirements.txt
pip install -r response_engine/requirements.txt
pip install -r forensics/requirements.txt
```

### Port Already in Use

If a port is already in use:
1. Find the process: `netstat -ano | findstr :9000`
2. Kill the process: `taskkill /PID <pid> /F`
3. Or change the port in the service configuration

### No Incidents Detected

1. Check Risk Engine logs for errors
2. Verify detector events are being sent (check dispatcher logs)
3. Check risk weights in `risk_engine/risk_weights.yaml`
4. Lower detection thresholds if needed
5. Wait a few seconds after running attack - processing takes time

### Dashboard Empty

1. Check if Risk Engine is running: `curl http://localhost:9000/incidents`
2. Check browser console for errors
3. Verify API URL in dashboard: `dashboard/src/api.js`
4. Check CORS settings if accessing from different host

## Service Ports

| Service | Port | Health Check |
|---------|------|--------------|
| Dispatcher | 8000 | http://localhost:8000/health |
| Network Detector | 8001 | http://localhost:8001/health |
| App Detector | 8002 | http://localhost:8002/health |
| Visual Detector | 8003 | http://localhost:8003/health |
| Risk Engine | 9000 | http://localhost:9000/health |
| Response Engine | 9200 | http://localhost:9200/health |
| Forensics | 9100 | http://localhost:9100/health |
| Blockchain Gateway | 8080 | http://localhost:8080/health |
| Dashboard | 3000 | http://localhost:3000 |

## Quick Verification

Test that all services are running:

```powershell
# Check all services
$services = @(8000, 8001, 8002, 8003, 9000, 9200, 9100, 8080)
foreach ($port in $services) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$port/health" -TimeoutSec 1
        Write-Host "✓ Port $port - OK" -ForegroundColor Green
    } catch {
        Write-Host "✗ Port $port - NOT RUNNING" -ForegroundColor Red
    }
}
```

## Next Steps

After successful setup:

1. **Run Attack**: `python scripts/demo_attack_simulator.py --attack clipboard`
2. **Check Incidents**: Open http://localhost:9000/incidents
3. **View Dashboard**: Open http://localhost:3000
4. **Review Logs**: Check terminal outputs for each service

## Demo Talking Points

1. "We intercept VNC traffic through our proxy"
2. "Three specialized detectors analyze different attack vectors"
3. "Risk Engine correlates events and calculates real-time risk scores"
4. "Automated response: HIGH risk = kill session, MEDIUM = deceive, LOW = allow"
5. "Forensics automatically collects evidence"
6. "Blockchain ensures evidence integrity"
7. "Dashboard provides real-time visibility"

