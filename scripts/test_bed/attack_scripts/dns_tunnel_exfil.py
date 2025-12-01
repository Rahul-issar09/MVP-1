#!/usr/bin/env python3
"""
DNS Tunneling Exfiltration Attack Simulation

Simulates an attacker using DNS queries as a covert channel.
This attack demonstrates how data can be exfiltrated via DNS
tunneling, which is difficult to detect.

Attack Pattern:
- Connects to VNC server through SentinelVNC proxy
- Sends small packets (60-120 bytes) in DNS-like patterns
- Uses timing patterns typical of DNS tunneling
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.vnc_client import VNCClient, create_vnc_client
from utils.attack_helpers import log_attack_step


def simulate_dns_tunnel_exfiltration(
    vnc_host: str,
    vnc_port: int,
    num_queries: int = 50,
    query_interval: float = 0.1
):
    """
    Simulate DNS tunneling-based data exfiltration.
    
    Args:
        vnc_host: VNC server hostname
        vnc_port: VNC server port
        num_queries: Number of DNS-like queries to send
        query_interval: Time between queries (seconds)
    """
    log_attack_step("Starting DNS Tunneling Exfiltration Attack", {
        "target": f"{vnc_host}:{vnc_port}",
        "num_queries": num_queries,
        "query_interval": f"{query_interval}s"
    })
    
    client = create_vnc_client(vnc_host, vnc_port)
    
    if not client.connect():
        print("ERROR: Failed to connect to VNC server")
        return False
    
    log_attack_step("Connection established")
    
    try:
        log_attack_step(f"Sending {num_queries} DNS-like queries")
        
        # Simulate DNS tunneling pattern
        if not client.simulate_dns_tunnel_pattern(num_queries):
            print("ERROR: Failed to send DNS tunnel packets")
            return False
        
        log_attack_step("DNS tunneling exfiltration attack completed")
        print("\n[SUCCESS] Attack simulation completed")
        print("Expected Detection: Network Detector should detect 'dns_tunnel_suspected'")
        print("Expected Response: Risk Engine should calculate risk score")
        print("Note: DNS tunneling uses small packets (60-120 bytes) which may require")
        print("      multiple queries to trigger detection threshold")
        
        return True
        
    except Exception as e:
        print(f"ERROR during attack: {e}")
        return False
    finally:
        client.disconnect()
        log_attack_step("Disconnected from VNC server")


def main():
    parser = argparse.ArgumentParser(
        description="Simulate DNS tunneling-based data exfiltration attack"
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
        "--num-queries",
        type=int,
        default=50,
        help="Number of DNS-like queries (default: 50)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.1,
        help="Interval between queries in seconds (default: 0.1)"
    )
    
    args = parser.parse_args()
    
    success = simulate_dns_tunnel_exfiltration(
        args.vnc_host,
        args.vnc_port,
        args.num_queries,
        args.interval
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

