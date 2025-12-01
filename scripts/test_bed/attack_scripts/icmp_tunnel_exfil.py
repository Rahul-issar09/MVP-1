#!/usr/bin/env python3
"""
ICMP Tunneling Exfiltration Attack Simulation

Simulates an attacker using ICMP packets as a covert channel.
This attack demonstrates how data can be exfiltrated via ICMP
tunneling, similar to DNS tunneling but using ICMP packets.

Attack Pattern:
- Connects to VNC server through SentinelVNC proxy
- Sends medium-sized packets (100-300 bytes) in ICMP-like patterns
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.vnc_client import VNCClient, create_vnc_client
from utils.attack_helpers import log_attack_step


def simulate_icmp_tunnel_exfiltration(
    vnc_host: str,
    vnc_port: int,
    num_packets: int = 30,
    packet_interval: float = 0.1
):
    """
    Simulate ICMP tunneling-based data exfiltration.
    
    Args:
        vnc_host: VNC server hostname
        vnc_port: VNC server port
        num_packets: Number of ICMP-like packets to send
        packet_interval: Time between packets (seconds)
    """
    log_attack_step("Starting ICMP Tunneling Exfiltration Attack", {
        "target": f"{vnc_host}:{vnc_port}",
        "num_packets": num_packets,
        "packet_interval": f"{packet_interval}s"
    })
    
    client = create_vnc_client(vnc_host, vnc_port)
    
    if not client.connect():
        print("ERROR: Failed to connect to VNC server")
        return False
    
    log_attack_step("Connection established")
    
    try:
        log_attack_step(f"Sending {num_packets} ICMP-like packets")
        
        # Simulate ICMP tunneling pattern
        if not client.simulate_icmp_tunnel_pattern(num_packets):
            print("ERROR: Failed to send ICMP tunnel packets")
            return False
        
        log_attack_step("ICMP tunneling exfiltration attack completed")
        print("\n[SUCCESS] Attack simulation completed")
        print("Expected Detection: Network Detector should detect 'icmp_tunnel_suspected'")
        print("Expected Response: Risk Engine should calculate risk score")
        
        return True
        
    except Exception as e:
        print(f"ERROR during attack: {e}")
        return False
    finally:
        client.disconnect()
        log_attack_step("Disconnected from VNC server")


def main():
    parser = argparse.ArgumentParser(
        description="Simulate ICMP tunneling-based data exfiltration attack"
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
        "--num-packets",
        type=int,
        default=30,
        help="Number of ICMP-like packets (default: 30)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.1,
        help="Interval between packets in seconds (default: 0.1)"
    )
    
    args = parser.parse_args()
    
    success = simulate_icmp_tunnel_exfiltration(
        args.vnc_host,
        args.vnc_port,
        args.num_packets,
        args.interval
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

