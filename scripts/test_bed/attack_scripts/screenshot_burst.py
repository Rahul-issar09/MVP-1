#!/usr/bin/env python3
"""
Screenshot Burst Exfiltration Attack Simulation

Simulates an attacker rapidly capturing screenshots to exfiltrate
visual information. This attack demonstrates how sensitive visual
data can be stolen through rapid screenshot capture.

Attack Pattern:
- Connects to VNC server through SentinelVNC proxy
- Sends large data chunks (2000+ bytes) rapidly
- Simulates screenshot capture bursts
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.vnc_client import VNCClient, create_vnc_client
from utils.attack_helpers import log_attack_step


def simulate_screenshot_burst_exfiltration(
    vnc_host: str,
    vnc_port: int,
    num_screenshots: int = 20,
    screenshot_size: int = 3000,
    burst_interval: float = 0.05
):
    """
    Simulate screenshot burst-based data exfiltration.
    
    Args:
        vnc_host: VNC server hostname
        vnc_port: VNC server port
        num_screenshots: Number of screenshots to capture
        screenshot_size: Size of each screenshot data (bytes)
        burst_interval: Time between screenshots (seconds)
    """
    log_attack_step("Starting Screenshot Burst Exfiltration Attack", {
        "target": f"{vnc_host}:{vnc_port}",
        "num_screenshots": num_screenshots,
        "screenshot_size": f"{screenshot_size} bytes",
        "interval": f"{burst_interval}s"
    })
    
    client = create_vnc_client(vnc_host, vnc_port)
    
    if not client.connect():
        print("ERROR: Failed to connect to VNC server")
        return False
    
    log_attack_step("Connection established")
    
    try:
        log_attack_step(f"Capturing {num_screenshots} screenshots in burst mode")
        
        # Simulate screenshot burst
        if not client.simulate_screenshot_burst(num_screenshots):
            print("ERROR: Failed to capture screenshots")
            return False
        
        log_attack_step("Screenshot burst exfiltration attack completed")
        print("\n[SUCCESS] Attack simulation completed")
        print("Expected Detection: Visual Detector should detect 'screenshot_burst_candidate'")
        print("Expected Response: Risk Engine should calculate risk score and trigger response")
        
        return True
        
    except Exception as e:
        print(f"ERROR during attack: {e}")
        return False
    finally:
        client.disconnect()
        log_attack_step("Disconnected from VNC server")


def main():
    parser = argparse.ArgumentParser(
        description="Simulate screenshot burst-based data exfiltration attack"
    )
    parser.add_argument(
        "--vnc-host",
        default="localhost",
        help="VNC server hostname (default: localhost)"
    )
    parser.add_argument(
        "--vnc-port",
        type=int,
        default=5900,
        help="VNC server port (default: 5900)"
    )
    parser.add_argument(
        "--num-screenshots",
        type=int,
        default=20,
        help="Number of screenshots to capture (default: 20)"
    )
    parser.add_argument(
        "--screenshot-size",
        type=int,
        default=3000,
        help="Size of each screenshot in bytes (default: 3000)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.05,
        help="Interval between screenshots in seconds (default: 0.05)"
    )
    
    args = parser.parse_args()
    
    success = simulate_screenshot_burst_exfiltration(
        args.vnc_host,
        args.vnc_port,
        args.num_screenshots,
        args.screenshot_size,
        args.interval
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

