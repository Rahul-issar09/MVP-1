#!/usr/bin/env python3
"""
Simple test script to validate SentinelVNC services and run a basic attack simulation.
This script checks if services are running and performs a simple test.
"""

import sys
import time
import httpx
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Service URLs
RISK_ENGINE_URL = "http://localhost:9000"
RESPONSE_ENGINE_URL = "http://localhost:9200"
FORENSICS_URL = "http://localhost:9100"
BLOCKCHAIN_URL = "http://localhost:8080"

def check_service(name, url, timeout=2.0):
    """Check if a service is running."""
    try:
        with httpx.Client(timeout=timeout) as client:
            # Try to connect (may not have health endpoint)
            resp = client.get(url, timeout=timeout)
            return True, resp.status_code
    except httpx.ConnectError:
        return False, "Connection refused"
    except httpx.TimeoutException:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)

def test_risk_engine():
    """Test Risk Engine by sending a detector event."""
    print("\n[TEST] Testing Risk Engine...")
    
    # Check if service is running
    is_running, status = check_service("Risk Engine", RISK_ENGINE_URL)
    if not is_running:
        print(f"  ✗ Risk Engine not running: {status}")
        return False
    
    print(f"  [OK] Risk Engine is running (status: {status})")
    
    # Send a test detector event
    test_event = {
        "event_id": "test-event-001",
        "session_id": "test-session-001",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "detector": "app",
        "type": "clipboard_spike_candidate",
        "confidence": 0.8,
        "details": {"length": 2000, "test": True},
        "artifact_refs": []
    }
    
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(f"{RISK_ENGINE_URL}/detector-events", json=test_event)
            if resp.status_code == 200:
                result = resp.json()
                print(f"  [OK] Test event sent successfully")
                print(f"    Incident created: {result.get('incident_created', False)}")
                return True
            else:
                print(f"  [FAIL] Failed to send event: {resp.status_code}")
                return False
    except Exception as e:
        print(f"  [FAIL] Error sending event: {e}")
        return False

def test_get_incidents():
    """Test getting incidents from Risk Engine."""
    print("\n[TEST] Testing incident retrieval...")
    
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{RISK_ENGINE_URL}/incidents")
            if resp.status_code == 200:
                incidents = resp.json()
                print(f"  [OK] Retrieved {len(incidents)} incident(s)")
                if incidents:
                    for i, incident in enumerate(incidents[:3], 1):  # Show first 3
                        print(f"    Incident {i}: {incident.get('incident_id')} "
                              f"(Risk: {incident.get('risk_score')}, "
                              f"Level: {incident.get('risk_level')})")
                return True
            else:
                print(f"  [FAIL] Failed to get incidents: {resp.status_code}")
                return False
    except Exception as e:
        print(f"  [FAIL] Error getting incidents: {e}")
        return False

def check_all_services():
    """Check all SentinelVNC services."""
    print("\n[CHECK] Checking SentinelVNC services...")
    
    services = [
        ("Risk Engine", RISK_ENGINE_URL),
        ("Response Engine", RESPONSE_ENGINE_URL),
        ("Forensics Service", FORENSICS_URL),
        ("Blockchain Gateway", BLOCKCHAIN_URL),
    ]
    
    all_running = True
    for name, url in services:
        is_running, status = check_service(name, url)
        if is_running:
            print(f"  [OK] {name} is running")
        else:
            print(f"  [FAIL] {name} is not running: {status}")
            all_running = False
    
    return all_running

def main():
    print("=" * 60)
    print("SentinelVNC Simple Test")
    print("=" * 60)
    
    # Check services
    services_ok = check_all_services()
    
    if not services_ok:
        print("\n[WARNING] Some services are not running.")
        print("Please start all services before running tests.")
        print("\nTo start services, see: scripts/test_bed/start_services.ps1")
        return 1
    
    # Test Risk Engine
    risk_ok = test_risk_engine()
    
    # Wait a moment for processing
    if risk_ok:
        time.sleep(1)
        test_get_incidents()
    
    print("\n" + "=" * 60)
    if risk_ok:
        print("[SUCCESS] Basic tests passed!")
        print("\nNext steps:")
        print("1. Run attack scenarios: python scripts/test_bed/attack_scripts/clipboard_exfil.py")
        print("2. Check incidents: python scripts/test_bed/validation/check_incidents.py")
    else:
        print("[FAILED] Some tests failed")
    print("=" * 60)
    
    return 0 if risk_ok else 1

if __name__ == "__main__":
    sys.exit(main())

