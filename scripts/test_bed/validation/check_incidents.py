#!/usr/bin/env python3
"""
Validation script to check if incidents were created after attack simulations.
"""

import argparse
import sys
import time
import httpx
from typing import List, Dict, Optional


RISK_ENGINE_URL = "http://localhost:9000"


def fetch_incidents() -> List[Dict]:
    """Fetch all incidents from Risk Engine."""
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{RISK_ENGINE_URL}/incidents")
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"ERROR: Failed to fetch incidents (status {resp.status_code})")
                return []
    except Exception as e:
        print(f"ERROR: Failed to connect to Risk Engine: {e}")
        print(f"Make sure Risk Engine is running at {RISK_ENGINE_URL}")
        return []


def filter_incidents_by_scenario(incidents: List[Dict], scenario: Optional[str] = None) -> List[Dict]:
    """Filter incidents by scenario type."""
    if not scenario:
        return incidents
    
    scenario_mapping = {
        "clipboard": ["clipboard_spike_candidate"],
        "file_transfer": ["file_transfer_candidate", "file_transfer_metadata"],
        "dns_tunnel": ["dns_tunnel_suspected"],
        "icmp_tunnel": ["icmp_tunnel_suspected"],
        "screenshot_burst": ["screenshot_burst_candidate"],
        "steganography": ["steganography_detected"],
    }
    
    event_types = scenario_mapping.get(scenario.lower(), [])
    if not event_types:
        return incidents
    
    filtered = []
    for incident in incidents:
        for event in incident.get("events", []):
            if event.get("type") in event_types:
                filtered.append(incident)
                break
    
    return filtered


def print_incident_summary(incidents: List[Dict]):
    """Print summary of incidents."""
    if not incidents:
        print("\n❌ No incidents found")
        return
    
    print(f"\n✅ Found {len(incidents)} incident(s)\n")
    
    for i, incident in enumerate(incidents, 1):
        print(f"Incident {i}:")
        print(f"  ID: {incident.get('incident_id')}")
        print(f"  Session ID: {incident.get('session_id')}")
        print(f"  Risk Score: {incident.get('risk_score')}")
        print(f"  Risk Level: {incident.get('risk_level')}")
        print(f"  Recommended Action: {incident.get('recommended_action')}")
        print(f"  Events: {len(incident.get('events', []))}")
        
        # Show event types
        event_types = [e.get('type') for e in incident.get('events', [])]
        if event_types:
            print(f"  Event Types: {', '.join(set(event_types))}")
        
        print()


def validate_detection(incidents: List[Dict], scenario: Optional[str] = None) -> bool:
    """Validate that detection occurred."""
    if not incidents:
        print("❌ Validation FAILED: No incidents detected")
        return False
    
    filtered = filter_incidents_by_scenario(incidents, scenario)
    
    if scenario and not filtered:
        print(f"❌ Validation FAILED: No incidents found for scenario '{scenario}'")
        return False
    
    # Check if any incident has high risk
    high_risk = any(i.get('risk_score', 0) >= 70 for i in filtered)
    medium_risk = any(30 <= i.get('risk_score', 0) < 70 for i in filtered)
    
    if high_risk:
        print("✅ Validation PASSED: High-risk incidents detected")
    elif medium_risk:
        print("✅ Validation PASSED: Medium-risk incidents detected")
    else:
        print("⚠️  Validation PARTIAL: Low-risk incidents detected")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Check if incidents were created after attack simulation"
    )
    parser.add_argument(
        "--scenario",
        choices=["clipboard", "file_transfer", "dns_tunnel", "icmp_tunnel", 
                 "screenshot_burst", "steganography"],
        help="Filter by scenario type"
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=0,
        help="Wait N seconds before checking (default: 0)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate detection (exit with error if no incidents)"
    )
    
    args = parser.parse_args()
    
    if args.wait > 0:
        print(f"Waiting {args.wait} seconds for incidents to be processed...")
        time.sleep(args.wait)
    
    print("Fetching incidents from Risk Engine...")
    incidents = fetch_incidents()
    
    if args.scenario:
        print(f"Filtering incidents for scenario: {args.scenario}")
        incidents = filter_incidents_by_scenario(incidents, args.scenario)
    
    print_incident_summary(incidents)
    
    if args.validate:
        success = validate_detection(incidents, args.scenario)
        sys.exit(0 if success else 1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

