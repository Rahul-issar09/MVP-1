# SentinelVNC Testing Guide

## Quick Test (Without VNC Server)

If you just want to test the detection system without setting up a VNC server:

### Step 1: Start Required Services

Open **5 separate PowerShell/Command Prompt windows** and run:

**Terminal 1 - Risk Engine:**
```powershell
cd risk_engine
uvicorn main:app --host 0.0.0.0 --port 9000
```

**Terminal 2 - Response Engine:**
```powershell
cd response_engine
uvicorn main:app --host 0.0.0.0 --port 9200
```

**Terminal 3 - Forensics Service:**
```powershell
cd forensics
uvicorn main:app --host 0.0.0.0 --port 9100
```

**Terminal 4 - Blockchain Gateway:**
```powershell
python -m uvicorn blockchain.gateway:app --host 0.0.0.0 --port 8080
```

**Terminal 5 - (Optional) Dashboard:**
```powershell
cd dashboard
npm run dev
```

### Step 2: Verify Services Are Running

Run the simple test script:

```powershell
python scripts\test_bed\test_simple.py
```

You should see:
```
[OK] Risk Engine is running
[OK] Response Engine is running
[OK] Forensics Service is running
[OK] Blockchain Gateway is running
```

### Step 3: Test Detection System

Send a test event directly to the Risk Engine:

```powershell
python scripts\test_bed\test_simple.py
```

This will:
1. Check all services
2. Send a test detector event
3. Check if an incident was created

### Step 4: View Incidents

Check if incidents were created:

```powershell
python scripts\test_bed\validation\check_incidents.py
```

Or view in the dashboard at: `http://localhost:3000`

## Full Test (With VNC Server)

For complete testing with actual VNC traffic:

### Prerequisites

1. **Install TigerVNC or RealVNC** (if not already installed)
   - Windows: Download from https://www.tigervnc.org/
   - Or use RealVNC: https://www.realvnc.com/

2. **Start VNC Server**
   ```powershell
   # TigerVNC example (if installed)
   vncserver :1
   ```

### Step 1: Start All Services

Follow the same steps as "Quick Test" above, plus:

**Terminal 6 - Proxy:**
```powershell
cd proxy
node index.js
```

### Step 2: Run Attack Scenarios

Run a single attack scenario:

```powershell
python scripts\test_bed\attack_scripts\clipboard_exfil.py --vnc-host localhost --vnc-port 5900
```

Or run all scenarios:

```powershell
# On Linux/Mac
cd scripts/test_bed
./run_all_scenarios.sh

# On Windows (PowerShell)
cd scripts\test_bed
python attack_scripts\clipboard_exfil.py --vnc-host localhost --vnc-port 5900
python attack_scripts\file_transfer_exfil.py --vnc-host localhost --vnc-port 5900
python attack_scripts\dns_tunnel_exfil.py --vnc-host localhost --vnc-port 5900
```

### Step 3: Validate Detection

After running an attack, check if it was detected:

```powershell
python scripts\test_bed\validation\check_incidents.py
```

For specific scenario:
```powershell
python scripts\test_bed\validation\check_incidents.py --scenario clipboard
```

## Testing Checklist

- [ ] All services started (Risk Engine, Response Engine, Forensics, Blockchain Gateway)
- [ ] Services verified with `test_simple.py`
- [ ] Test event sent successfully
- [ ] Incident created in Risk Engine
- [ ] Dashboard shows incidents (if running)
- [ ] Attack scenarios run (if VNC server available)
- [ ] Detection validated with `check_incidents.py`

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
2. Verify detector events are being sent
3. Check risk weights in `risk_engine/risk_weights.yaml`
4. Lower detection thresholds if needed

### VNC Connection Issues

1. Verify VNC server is running: `netstat -an | findstr 5900`
2. Check firewall settings
3. Verify proxy is intercepting traffic
4. Check proxy logs for connection errors

## Next Steps

After successful testing:

1. **Review Incidents**: Check the dashboard or use validation scripts
2. **Analyze Detection**: Review which events triggered incidents
3. **Tune Thresholds**: Adjust `risk_weights.yaml` if needed
4. **Run Full Test Suite**: Execute all attack scenarios
5. **Document Results**: Note any issues or improvements needed

## Quick Reference

| Service | Port | Command |
|---------|------|---------|
| Risk Engine | 9000 | `cd risk_engine && uvicorn main:app --port 9000` |
| Response Engine | 9200 | `cd response_engine && uvicorn main:app --port 9200` |
| Forensics | 9100 | `cd forensics && uvicorn main:app --port 9100` |
| Blockchain Gateway | 8080 | `python -m uvicorn blockchain.gateway:app --port 8080` |
| Proxy | 5900 | `cd proxy && node index.js` |
| Dashboard | 3000 | `cd dashboard && npm run dev` |

## Test Scripts

- **Simple Test**: `python scripts\test_bed\test_simple.py`
- **Check Incidents**: `python scripts\test_bed\validation\check_incidents.py`
- **Verify Detection**: `python scripts\test_bed\validation\verify_detection.py`
- **Clipboard Attack**: `python scripts\test_bed\attack_scripts\clipboard_exfil.py`
- **File Transfer Attack**: `python scripts\test_bed\attack_scripts\file_transfer_exfil.py`

For more details, see: `scripts/test_bed/TEST_BED_GUIDE.md`


