# Complete End-to-End Testing Guide

## Overview
This guide will help you test the complete SentinelVNC flow from attack simulation to dashboard display.

---

## Prerequisites

### 1. Check All Services Are Running

Open **8 separate terminals** and start each service:

**Terminal 1 - Dispatcher:**
```powershell
cd detectors
uvicorn dispatcher:app --host 0.0.0.0 --port 8000
```
**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
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

---

## Step 1: Verify All Services Are Running

### Test Health Endpoints

Run this in a new terminal:

```powershell
python scripts/test_demo_flow.py
```

**Expected Output:**
```
============================================================
Testing SentinelVNC Demo Flow
============================================================

[1] Checking services...
  ✓ Dispatcher
  ✓ Network Detector
  ✓ App Detector
  ✓ Visual Detector
  ✓ Risk Engine
  ✓ Response Engine
  ✓ Forensics
  ✓ Blockchain Gateway
```

**✅ Success Criteria:** All 8 services show ✓

**❌ If any service fails:**
- Check that service is running in its terminal
- Check for port conflicts
- Verify the service started without errors

---

## Step 2: Run Attack Simulation

### Option A: Automated Test (Recommended)

```powershell
python scripts/test_demo_flow.py
```

**Expected Output:**
```
[2] Sending test attack...

🔴 [ATTACK] Clipboard Exfiltration Attack
   Session: abc12345...
   Intensity: high
   Performing 15 clipboard operations...
   ✓ Operation 1/15 - 3000 bytes
   ✓ Operation 5/15 - 3000 bytes
   ✓ Operation 10/15 - 3000 bytes
   ✓ Operation 15/15 - 3000 bytes
   ✓ Completed 15/15 operations successfully
   ✅ Attack complete!
   Expected: App Detector → clipboard_spike_candidate
   Expected: Risk Engine → HIGH risk → kill_session
  ✓ Attack sent (session: abc12345...)
```

**✅ Success Criteria:**
- At least 10+ operations succeed
- No timeout errors
- Attack completes

### Option B: Manual Attack

```powershell
python scripts/demo_attack_simulator.py --attack clipboard --intensity high
```

**Expected Output:** Same as above

---

## Step 3: Verify Detection in Detectors

### Check Dispatcher Logs (Terminal 1)

**Expected Output:**
```
INFO:     127.0.0.1:xxxxx - "POST /events HTTP/1.1" 200 OK
INFO:     Routed app_stream (session=abc12345, length=3000) to app detector
```

**✅ Success Criteria:** See multiple routing messages

### Check App Detector Logs (Terminal 3)

**Expected Output:**
```
INFO:     Received app event from 127.0.0.1: session_id=abc12345... length=3000 direction=client_to_server
INFO:     app detector_event: {'event_id': '...', 'type': 'clipboard_spike_candidate', 'confidence': 0.2, ...}
```

**✅ Success Criteria:**
- See "Received app event" messages
- See "clipboard_spike_candidate" events
- Events sent to Risk Engine

---

## Step 4: Verify Risk Engine Processing

### Check Risk Engine Logs (Terminal 5)

**Expected Output:**
```
INFO:     POST /detector-events HTTP/1.1 200 OK
INFO:     Created incident abc-123-def-456 for session abc12345 (score=75, level=HIGH)
```

**✅ Success Criteria:**
- See "Created incident" messages
- Risk score > 30 (should be HIGH for clipboard attack)
- Risk level is HIGH or MEDIUM

### Check via API

```powershell
curl http://localhost:9000/incidents
```

**Expected Output (JSON):**
```json
[
  {
    "incident_id": "abc-123-def-456",
    "session_id": "abc12345...",
    "risk_score": 75,
    "risk_level": "HIGH",
    "recommended_action": "kill_session",
    "events": [
      {
        "event_id": "...",
        "detector": "app",
        "type": "clipboard_spike_candidate",
        "confidence": 0.2
      }
    ]
  }
]
```

**✅ Success Criteria:**
- At least 1 incident in array
- Risk score > 30
- Events array contains detector events

---

## Step 5: Verify Response Engine

### Check Response Engine Logs (Terminal 6)

**Expected Output:**
```
INFO:     [response] received incident=abc-123-def-456 session_id=abc12345... risk_score=75 action=kill_session
INFO:     [response] kill_session requested for session_id=abc12345...
INFO:     [response] proxy kill_session response status=200 body={"status":"terminated"}
INFO:     [response] forensics/start response status=200
```

**✅ Success Criteria:**
- See "received incident" message
- See action being taken (kill_session/deceive/allow)
- Forensics collection initiated

---

## Step 6: Verify Forensics Collection

### Check Forensics Logs (Terminal 7)

**Expected Output:**
```
INFO:     POST /forensics/start HTTP/1.1 200 OK
INFO:     Collected artifacts for incident abc-123-def-456
```

**✅ Success Criteria:**
- Forensics collection started
- Artifacts collected

---

## Step 7: Verify Dashboard Display

### Open Dashboard

1. Open browser: http://localhost:3000

2. **Expected Dashboard View:**
   - **Stats Cards** showing:
     - Active Incidents: 1+
     - Critical: 1+ (if HIGH risk)
     - Avg Risk Score: 50-100
     - Total Incidents: 1+

3. **Click on an Incident:**
   - **Expected Details:**
     - Incident ID displayed
     - Risk Score: 50-100
     - Risk Level: HIGH/MEDIUM
     - Status: active/investigating
     - Event Count: 10-15 events
     - Events List showing:
       - Type: clipboard_spike_candidate
       - Source: App Detector
       - Timestamp: Recent
       - Confidence: 0.2

**✅ Success Criteria:**
- Dashboard loads without errors
- Incidents appear in list
- Can click and view incident details
- Events are displayed
- No CORS errors in browser console (F12)

---

## Step 8: Verify Risk Explanation

### Check Risk Explanation API

```powershell
curl http://localhost:9000/incidents/{incident_id}/explanation
```

Replace `{incident_id}` with actual incident ID from Step 4.

**Expected Output (JSON):**
```json
{
  "total_score": 75,
  "top_contributors": [
    {
      "type": "clipboard_spike_candidate",
      "score": 45
    },
    {
      "type": "app_activity",
      "score": 30
    }
  ]
}
```

**✅ Success Criteria:**
- Total score matches incident risk score
- Top contributors show event types
- Scores add up to total

---

## Step 9: Test Different Attack Types

### Test File Transfer Attack

```powershell
python scripts/demo_attack_simulator.py --attack file --intensity high
```

**Expected:**
- Network Detector receives events
- Event type: `file_transfer_candidate`
- Risk Engine creates incident
- Dashboard shows new incident

### Test DNS Tunneling Attack

```powershell
python scripts/demo_attack_simulator.py --attack dns --intensity high
```

**Expected:**
- Network Detector receives events
- Event type: `dns_tunnel_suspected`
- Risk Engine creates incident

### Test Screenshot Burst Attack

```powershell
python scripts/demo_attack_simulator.py --attack screenshot --intensity high
```

**Expected:**
- Visual Detector receives events
- Event type: `screenshot_burst_candidate`
- Risk Engine creates incident

---

## Step 10: Complete Flow Verification

### Run Full Test Script

```powershell
python scripts/test_demo_flow.py
```

**Expected Complete Output:**
```
============================================================
Testing SentinelVNC Demo Flow
============================================================

[1] Checking services...
  ✓ Dispatcher
  ✓ Network Detector
  ✓ App Detector
  ✓ Visual Detector
  ✓ Risk Engine
  ✓ Response Engine
  ✓ Forensics
  ✓ Blockchain Gateway

[2] Sending test attack...
  ✓ Attack sent (session: abc12345...)

[3] Waiting for processing...
  (3 second wait)

[4] Checking incidents...
  ✓ Found 1 incident(s)

  Latest Incident:
    ID: abc-123-def-456
    Risk Score: 75
    Risk Level: HIGH
    Action: kill_session
    Events: 15

[5] Checking risk explanation...
  ✓ Risk explanation retrieved
    Total Score: 75
    Top Contributors:
      - clipboard_spike_candidate: 45
      - app_activity: 30

============================================================
✅ Demo flow test completed!

Next steps:
  1. View dashboard: http://localhost:3000
  2. Check API: http://localhost:9000/incidents
============================================================
```

**✅ Success Criteria:**
- All steps complete
- Incident created
- Risk explanation retrieved
- No errors

---

## Troubleshooting

### Issue: Services Not Starting

**Symptoms:** Health checks fail

**Solution:**
1. Check if ports are already in use:
   ```powershell
   netstat -ano | findstr :9000
   ```
2. Kill process if needed:
   ```powershell
   taskkill /PID <pid> /F
   ```
3. Check Python/Node versions
4. Install dependencies:
   ```powershell
   pip install -r detectors/requirements.txt
   pip install -r risk_engine/requirements.txt
   ```

### Issue: No Incidents Created

**Symptoms:** Attack runs but no incidents in API

**Solution:**
1. Check Risk Engine logs for errors
2. Verify risk weights in `risk_engine/risk_weights.yaml`
3. Lower thresholds if needed
4. Wait longer (processing takes 2-5 seconds)
5. Check detector events are reaching Risk Engine

### Issue: Dashboard Shows No Data

**Symptoms:** Dashboard loads but shows 0 incidents

**Solution:**
1. Check browser console (F12) for errors
2. Verify Risk Engine is running: `curl http://localhost:9000/incidents`
3. Check CORS is enabled (should be fixed)
4. Verify API URL in dashboard: `dashboard/src/api.js`
5. Hard refresh browser (Ctrl+F5)

### Issue: Timeout Errors

**Symptoms:** "Timeout sending event" messages

**Solution:**
1. Check dispatcher is running
2. Check detectors are running
3. Increase timeout in `scripts/demo_attack_simulator.py` if needed
4. Some timeouts are OK - events may still be processed

---

## Quick Verification Checklist

- [ ] All 8 services running (health checks pass)
- [ ] Attack simulator sends events successfully
- [ ] Dispatcher routes events to detectors
- [ ] Detectors receive and process events
- [ ] Risk Engine creates incidents
- [ ] Response Engine takes actions
- [ ] Forensics collects artifacts
- [ ] Dashboard displays incidents
- [ ] Dashboard shows event details
- [ ] Risk explanations work
- [ ] No CORS errors in browser
- [ ] No timeout errors (or minimal)

---

## Expected Flow Summary

```
1. Attack Simulator
   ↓ Sends events to Dispatcher
2. Dispatcher
   ↓ Routes to appropriate Detector
3. Detector (App/Network/Visual)
   ↓ Analyzes and sends to Risk Engine
4. Risk Engine
   ↓ Creates incident with risk score
   ↓ Sends to Response Engine
5. Response Engine
   ↓ Takes action (kill/deceive/allow)
   ↓ Triggers Forensics
6. Forensics
   ↓ Collects artifacts
7. Dashboard
   ↓ Displays incidents in real-time
```

---

## Success Indicators

✅ **All Green:**
- All services running
- Events flowing through system
- Incidents created
- Dashboard showing data
- No errors in logs

⚠️ **Partial Success:**
- Some events timeout (OK if most succeed)
- Some services slow (check resources)
- Dashboard shows mock data (check API connection)

❌ **Failure:**
- Services not starting
- No incidents created
- Dashboard shows errors
- CORS errors persist

---

## Next Steps After Testing

1. **If everything works:** You're ready for demo! 🎉
2. **If issues found:** Check troubleshooting section
3. **For production:** Review security settings (CORS origins, API keys)

---

## Quick Test Command

For fastest verification, run:

```powershell
python scripts/test_demo_flow.py
```

This tests the complete flow automatically and reports results.

