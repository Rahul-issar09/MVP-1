#!/usr/bin/env python3
"""Diagnostic script to check why incidents aren't appearing."""
import httpx
import sys
from pathlib import Path

def diagnose():
    print("=" * 60)
    print("SentinelVNC Incident Diagnostic Tool")
    print("=" * 60)
    
    # 1. Check Risk Engine health
    print("\n[1] Checking Risk Engine health...")
    try:
        resp = httpx.get("http://localhost:9000/health", timeout=5)
        if resp.status_code == 200:
            print("  ✓ Risk Engine is running")
        else:
            print(f"  ✗ Risk Engine returned status {resp.status_code}")
            return
    except Exception as e:
        print(f"  ✗ Cannot connect to Risk Engine: {e}")
        print("     Make sure Risk Engine is running: uvicorn risk_engine.main:app --host 0.0.0.0 --port 9000")
        return
    
    # 2. Check incidents endpoint
    print("\n[2] Checking /incidents endpoint...")
    try:
        resp = httpx.get("http://localhost:9000/incidents", timeout=10)
        if resp.status_code == 200:
            incidents = resp.json()
            print(f"  ✓ Endpoint accessible")
            print(f"  ✓ Found {len(incidents)} incident(s)")
            
            if incidents:
                print("\n  Recent Incidents:")
                for i, inc in enumerate(incidents[:5], 1):
                    print(f"    {i}. ID: {inc.get('incident_id', 'N/A')[:8]}...")
                    print(f"       Risk: {inc.get('risk_score', 'N/A')} ({inc.get('risk_level', 'N/A')})")
                    print(f"       Events: {len(inc.get('events', []))}")
                    print(f"       Action: {inc.get('recommended_action', 'N/A')}")
            else:
                print("  ⚠ No incidents found")
                print("\n  Possible reasons:")
                print("    - No attacks have been sent yet")
                print("    - Events didn't reach the Risk Engine")
                print("    - Risk threshold wasn't met")
        else:
            print(f"  ✗ Endpoint returned status {resp.status_code}")
            print(f"     Response: {resp.text[:200]}")
    except httpx.TimeoutException:
        print("  ✗ Timeout - Risk Engine is not responding")
        print("     The /incidents endpoint may be hanging")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Check if detectors are sending events
    print("\n[3] Checking detector services...")
    detectors = [
        ("Network Detector", "http://localhost:8001/health"),
        ("App Detector", "http://localhost:8002/health"),
        ("Visual Detector", "http://localhost:8003/health"),
    ]
    
    for name, url in detectors:
        try:
            resp = httpx.get(url, timeout=2)
            if resp.status_code == 200:
                print(f"  ✓ {name} is running")
            else:
                print(f"  ⚠ {name} returned status {resp.status_code}")
        except Exception as e:
            print(f"  ✗ {name} is not running: {e}")
    
    # 4. Check dispatcher
    print("\n[4] Checking dispatcher...")
    try:
        resp = httpx.get("http://localhost:8000/health", timeout=2)
        if resp.status_code == 200:
            print("  ✓ Dispatcher is running")
        else:
            print(f"  ⚠ Dispatcher returned status {resp.status_code}")
    except Exception as e:
        print(f"  ✗ Dispatcher is not running: {e}")
    
    print("\n" + "=" * 60)
    print("Diagnostic complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. If no incidents: Run an attack simulation")
    print("     python scripts/demo_attack_simulator.py")
    print("  2. Check Risk Engine logs for errors")
    print("  3. Verify events are reaching detectors")
    print("  4. Check dispatcher logs for routing issues")

if __name__ == "__main__":
    diagnose()

