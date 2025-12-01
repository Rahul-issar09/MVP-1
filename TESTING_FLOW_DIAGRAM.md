# Testing Flow - Input/Output at Each Step

## Complete Flow Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 1: START SERVICES                       │
└─────────────────────────────────────────────────────────────────┘
INPUT:  Start 8 services in separate terminals
OUTPUT: All services running, health checks pass
        ✓ Dispatcher (8000)
        ✓ Network Detector (8001)
        ✓ App Detector (8002)
        ✓ Visual Detector (8003)
        ✓ Risk Engine (9000)
        ✓ Response Engine (9200)
        ✓ Forensics (9100)
        ✓ Blockchain Gateway (8080)

┌─────────────────────────────────────────────────────────────────┐
│              STEP 2: RUN ATTACK SIMULATION                      │
└─────────────────────────────────────────────────────────────────┘
INPUT:  python scripts/demo_attack_simulator.py --attack clipboard
OUTPUT: 
        🔴 [ATTACK] Clipboard Exfiltration Attack
           Session: abc12345...
           Performing 15 clipboard operations...
           ✓ Operation 1/15 - 3000 bytes
           ✓ Operation 5/15 - 3000 bytes
           ...
           ✓ Completed 15/15 operations successfully
           ✅ Attack complete!

┌─────────────────────────────────────────────────────────────────┐
│              STEP 3: DISPATCHER ROUTES EVENTS                   │
└─────────────────────────────────────────────────────────────────┘
INPUT:  Events from attack simulator
OUTPUT: Dispatcher logs show:
        INFO: Routed app_stream (session=abc12345, length=3000) to app detector
        INFO: POST /events HTTP/1.1 200 OK

┌─────────────────────────────────────────────────────────────────┐
│              STEP 4: DETECTORS ANALYZE EVENTS                   │
└─────────────────────────────────────────────────────────────────┘
INPUT:  Events from dispatcher
OUTPUT: App Detector logs show:
        INFO: Received app event: session_id=abc12345... length=3000
        INFO: app detector_event: {
              'type': 'clipboard_spike_candidate',
              'confidence': 0.2,
              'detector': 'app'
            }
        INFO: Sent to Risk Engine

┌─────────────────────────────────────────────────────────────────┐
│              STEP 5: RISK ENGINE CREATES INCIDENT               │
└─────────────────────────────────────────────────────────────────┘
INPUT:  Detector events from all detectors
OUTPUT: Risk Engine logs show:
        INFO: Created incident abc-123-def-456 for session abc12345
              (score=75, level=HIGH)
        
        API Response (GET /incidents):
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
                "confidence": 0.2,
                "timestamp": "2025-01-XX..."
              }
            ]
          }
        ]

┌─────────────────────────────────────────────────────────────────┐
│              STEP 6: RESPONSE ENGINE TAKES ACTION               │
└─────────────────────────────────────────────────────────────────┘
INPUT:  Incident from Risk Engine
OUTPUT: Response Engine logs show:
        INFO: [response] received incident=abc-123-def-456
              risk_score=75 action=kill_session
        INFO: [response] kill_session requested for session_id=abc12345...
        INFO: [response] proxy kill_session response status=200
        INFO: [response] forensics/start response status=200

┌─────────────────────────────────────────────────────────────────┐
│              STEP 7: FORENSICS COLLECTS ARTIFACTS               │
└─────────────────────────────────────────────────────────────────┘
INPUT:  Forensics request from Response Engine
OUTPUT: Forensics logs show:
        INFO: POST /forensics/start HTTP/1.1 200 OK
        INFO: Collected artifacts for incident abc-123-def-456
        Artifacts stored in: forensics/data/inc-abc-123-def-456/

┌─────────────────────────────────────────────────────────────────┐
│              STEP 8: DASHBOARD DISPLAYS RESULTS                 │
└─────────────────────────────────────────────────────────────────┘
INPUT:  API call to http://localhost:9000/incidents
OUTPUT: Dashboard shows:
        - Stats Cards:
          * Active Incidents: 1
          * Critical: 1
          * Avg Risk Score: 75%
          * Total Incidents: 1
        
        - Incident List:
          * Incident with risk score 75
          * Status: active
          * Severity: critical
        
        - Incident Details (on click):
          * Event Timeline: 15 events
          * Event Types: clipboard_spike_candidate
          * Risk Breakdown: Shows contributing events
          * Response Action: kill_session

┌─────────────────────────────────────────────────────────────────┐
│              STEP 9: VERIFY RISK EXPLANATION                    │
└─────────────────────────────────────────────────────────────────┘
INPUT:  GET /incidents/{incident_id}/explanation
OUTPUT: 
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

┌─────────────────────────────────────────────────────────────────┐
│                    EXPECTED VALUES SUMMARY                      │
└─────────────────────────────────────────────────────────────────┘

Service Health Checks:
  ✓ All 8 services return 200 OK

Attack Simulation:
  ✓ 10+ events sent successfully
  ✓ No critical timeout errors

Detector Events:
  ✓ App Detector: clipboard_spike_candidate events
  ✓ Network Detector: file_transfer_candidate events (if file attack)
  ✓ Visual Detector: screenshot_burst_candidate events (if screenshot attack)

Risk Engine:
  ✓ At least 1 incident created
  ✓ Risk score: 30-100 (depends on attack intensity)
  ✓ Risk level: MEDIUM or HIGH
  ✓ Events array: 10-15 events

Response Engine:
  ✓ Action taken: kill_session (HIGH) or deceive (MEDIUM)
  ✓ Forensics triggered

Dashboard:
  ✓ Loads without errors
  ✓ Shows incidents
  ✓ Displays event details
  ✓ No CORS errors in console

┌─────────────────────────────────────────────────────────────────┐
│                    COMMON ISSUES & FIXES                        │
└─────────────────────────────────────────────────────────────────┘

Issue: No incidents created
Fix: Check risk_weights.yaml, wait 3-5 seconds, verify events reaching Risk Engine

Issue: Dashboard shows 0 incidents
Fix: Check API connection, verify Risk Engine running, check CORS enabled

Issue: Timeout errors
Fix: Some timeouts OK, check dispatcher/detectors running, increase timeout if needed

Issue: CORS errors
Fix: Restart Risk Engine (CORS middleware added), check browser console

