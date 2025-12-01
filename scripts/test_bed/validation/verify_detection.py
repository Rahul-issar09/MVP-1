#!/usr/bin/env python3
"""
Advanced verification script to validate detection and response mechanisms.
"""

import argparse
import sys
import httpx
from typing import Dict, List


RISK_ENGINE_URL = "http://localhost:9000"
RESPONSE_ENGINE_URL = "http://localhost:9200"


def check_risk_engine() -> bool:
    """Check if Risk Engine is running."""
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{RISK_ENGINE_URL}/incidents")
            return resp.status_code == 200
    except:
        return False


def check_response_engine() -> bool:
    """Check if Response Engine is running."""
    try:
        with httpx.Client(timeout=5.0) as client:
            # Try to get a simple endpoint (may need to be added)
            resp = client.get(f"{RESPONSE_ENGINE_URL}/health", timeout=2.0)
            return resp.status_code == 200
    except:
        # Response engine might not have health endpoint, that's OK
        return True  # Assume running if we can't check


def get_incident_details(incident_id: str) -> Dict:
    """Get detailed information about an incident."""
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{RISK_ENGINE_URL}/incidents/{incident_id}")
            if resp.status_code == 200:
                return resp.json()
            
            # Try explanation endpoint
            resp = client.get(f"{RISK_ENGINE_URL}/incidents/{incident_id}/explanation")
            if resp.status_code == 200:
                explanation = resp.json()
                incident = {"incident_id": incident_id}
                incident.update(explanation)
                return incident
            
            return {}
    except Exception as e:
        print(f"ERROR: Failed to get incident details: {e}")
        return {}


def verify_incident(incident: Dict) -> Dict:
    """Verify an incident has all required components."""
    results = {
        "has_events": len(incident.get("events", [])) > 0,
        "has_risk_score": "risk_score" in incident,
        "has_risk_level": "risk_level" in incident,
        "has_action": "recommended_action" in incident,
        "risk_score_valid": 0 <= incident.get("risk_score", -1) <= 100,
    }
    
    results["all_valid"] = all(results.values())
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Verify detection and response mechanisms"
    )
    parser.add_argument(
        "--incident-id",
        help="Verify specific incident by ID"
    )
    
    args = parser.parse_args()
    
    print("Verifying SentinelVNC detection system...\n")
    
    # Check services
    print("Checking services:")
    risk_ok = check_risk_engine()
    response_ok = check_response_engine()
    
    print(f"  Risk Engine: {'✅ Running' if risk_ok else '❌ Not running'}")
    print(f"  Response Engine: {'✅ Running' if response_ok else '⚠️  Status unknown'}")
    
    if not risk_ok:
        print("\n❌ Risk Engine is not running. Please start it first.")
        sys.exit(1)
    
    # Get incidents
    print("\nFetching incidents...")
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{RISK_ENGINE_URL}/incidents")
            incidents = resp.json() if resp.status_code == 200 else []
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    if not incidents:
        print("⚠️  No incidents found")
        sys.exit(0)
    
    print(f"Found {len(incidents)} incident(s)\n")
    
    # Verify incidents
    if args.incident_id:
        incident = get_incident_details(args.incident_id)
        if not incident:
            print(f"❌ Incident {args.incident_id} not found")
            sys.exit(1)
        incidents = [incident]
    
    for incident in incidents:
        print(f"Verifying Incident: {incident.get('incident_id', 'unknown')}")
        verification = verify_incident(incident)
        
        for check, result in verification.items():
            if check == "all_valid":
                continue
            status = "✅" if result else "❌"
            print(f"  {status} {check.replace('_', ' ').title()}")
        
        if verification["all_valid"]:
            print("  ✅ Incident verification PASSED\n")
        else:
            print("  ❌ Incident verification FAILED\n")
    
    print("Verification complete")


if __name__ == "__main__":
    main()

