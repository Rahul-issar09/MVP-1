#!/usr/bin/env python3
"""
Realistic VNC attack simulator for demo.
Sends events directly to dispatcher to simulate attacks.
This allows demonstration of the complete detection and response flow.
"""

import argparse
import time
import httpx
import uuid
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

DISPATCHER_URL = "http://localhost:8000/events"


def send_proxy_event(session_id, stream, direction, length):
    """Send a proxy event through dispatcher."""
    event = {
        "session_id": session_id,
        "ts": datetime.utcnow().isoformat() + "Z",
        "stream": stream,
        "direction": direction,
        "type": "raw_chunk",
        "length": length
    }
    
    try:
        # Increased timeout since dispatcher now returns immediately
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(DISPATCHER_URL, json=event)
            if resp.status_code == 200:
                return True
            else:
                print(f"  ⚠ HTTP {resp.status_code}: {resp.text[:50]}")
                return False
    except httpx.TimeoutException:
        print(f"  ⚠ Timeout sending event")
        return False
    except httpx.ConnectError:
        print(f"  ⚠ Cannot connect to dispatcher at {DISPATCHER_URL}")
        return False
    except Exception as e:
        print(f"  ⚠ Error: {str(e)[:50]}")
        return False


def simulate_clipboard_attack(intensity="high"):
    """Simulate clipboard exfiltration - triggers app detector."""
    session_id = str(uuid.uuid4())
    print(f"\n🔴 [ATTACK] Clipboard Exfiltration Attack")
    print(f"   Session: {session_id[:8]}...")
    print(f"   Intensity: {intensity}")
    
    params = {
        "low": {"ops": 5, "size": 1500, "delay": 0.5},
        "medium": {"ops": 10, "size": 2000, "delay": 0.3},
        "high": {"ops": 15, "size": 3000, "delay": 0.2}
    }
    p = params[intensity]
    
    print(f"   Performing {p['ops']} clipboard operations...")
    success_count = 0
    for i in range(p['ops']):
        success = send_proxy_event(session_id, "app_stream", "client_to_server", p['size'])
        if success:
            success_count += 1
            if (i + 1) % 5 == 0 or i == 0:  # Print every 5th or first
                print(f"   ✓ Operation {i+1}/{p['ops']} - {p['size']} bytes")
        time.sleep(p['delay'])
    
    print(f"   ✓ Completed {success_count}/{p['ops']} operations successfully")
    
    print(f"   ✅ Attack complete!")
    print(f"   Expected: App Detector → clipboard_spike_candidate")
    print(f"   Expected: Risk Engine → HIGH risk → kill_session")
    return session_id


def simulate_file_transfer_attack(intensity="high"):
    """Simulate file transfer - triggers network detector."""
    session_id = str(uuid.uuid4())
    print(f"\n🔴 [ATTACK] File Transfer Exfiltration")
    print(f"   Session: {session_id[:8]}...")
    
    sizes = [50000, 75000, 100000] if intensity == "high" else [30000, 40000]
    
    for i, size in enumerate(sizes):
        success = send_proxy_event(session_id, "network_stream", "client_to_server", size)
        if success:
            print(f"   ✓ Transfer {i+1}/{len(sizes)} - {size:,} bytes")
        time.sleep(0.3)  # Reduced delay
    
    print(f"   ✅ Attack complete!")
    print(f"   Expected: Network Detector → file_transfer_candidate")
    return session_id


def simulate_dns_tunnel_attack(intensity="high"):
    """Simulate DNS tunneling - triggers network detector."""
    session_id = str(uuid.uuid4())
    print(f"\n🔴 [ATTACK] DNS Tunneling Attack")
    print(f"   Session: {session_id[:8]}...")
    
    count = 50 if intensity == "high" else 30
    print(f"   Sending {count} DNS queries...")
    
    success_count = 0
    for i in range(count):
        if send_proxy_event(session_id, "network_stream", "client_to_server", 80):
            success_count += 1
        if (i + 1) % 10 == 0:
            print(f"   ✓ Sent {i+1}/{count} queries ({success_count} successful)")
        time.sleep(0.05)  # Reduced delay
    
    print(f"   ✅ Attack complete!")
    print(f"   Expected: Network Detector → dns_tunnel_suspected")
    return session_id


def simulate_screenshot_burst(intensity="high"):
    """Simulate screenshot burst - triggers visual detector."""
    session_id = str(uuid.uuid4())
    print(f"\n🔴 [ATTACK] Screenshot Burst Attack")
    print(f"   Session: {session_id[:8]}...")
    
    count = 20 if intensity == "high" else 10
    print(f"   Capturing {count} screenshots...")
    
    success_count = 0
    for i in range(count):
        if send_proxy_event(session_id, "visual_stream", "client_to_server", 3000):
            success_count += 1
        if (i + 1) % 5 == 0:
            print(f"   ✓ Captured {i+1}/{count} screenshots ({success_count} successful)")
        time.sleep(0.03)  # Reduced delay
    
    print(f"   ✅ Attack complete!")
    print(f"   Expected: Visual Detector → screenshot_burst_candidate")
    return session_id


def check_dispatcher():
    """Check if dispatcher is running."""
    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.get("http://localhost:8000/health")
            return resp.status_code == 200
    except:
        return False


def main():
    parser = argparse.ArgumentParser(description="VNC Attack Simulator for Demo")
    parser.add_argument("--attack", choices=["clipboard", "file", "dns", "screenshot", "all"],
                       default="clipboard", help="Attack type")
    parser.add_argument("--intensity", choices=["low", "medium", "high"],
                       default="high", help="Attack intensity")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("SentinelVNC Attack Simulator")
    print("=" * 60)
    
    # Check dispatcher
    if not check_dispatcher():
        print("\n❌ ERROR: Dispatcher not running at http://localhost:8000")
        print("   Please start the dispatcher first:")
        print("   cd detectors")
        print("   uvicorn dispatcher:app --host 0.0.0.0 --port 8000")
        return 1
    
    print("✓ Dispatcher is running")
    
    sessions = []
    
    if args.attack == "all":
        sessions.append(simulate_clipboard_attack(args.intensity))
        time.sleep(2)
        sessions.append(simulate_file_transfer_attack(args.intensity))
        time.sleep(2)
        sessions.append(simulate_dns_tunnel_attack(args.intensity))
        time.sleep(2)
        sessions.append(simulate_screenshot_burst(args.intensity))
    elif args.attack == "clipboard":
        sessions.append(simulate_clipboard_attack(args.intensity))
    elif args.attack == "file":
        sessions.append(simulate_file_transfer_attack(args.intensity))
    elif args.attack == "dns":
        sessions.append(simulate_dns_tunnel_attack(args.intensity))
    elif args.attack == "screenshot":
        sessions.append(simulate_screenshot_burst(args.intensity))
    
    print("\n" + "=" * 60)
    print("✅ Attack Simulation Complete!")
    print("=" * 60)
    print(f"\nSessions: {len(sessions)}")
    print("\n⏳ Waiting 3 seconds for processing...")
    time.sleep(3)
    print("\n📊 Check results:")
    print("   Dashboard: http://localhost:3000")
    print("   API: http://localhost:9000/incidents")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

