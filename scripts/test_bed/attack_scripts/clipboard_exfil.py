#!/usr/bin/env python3
"""
Clipboard Exfiltration Attack Simulation

Simulates an attacker copying sensitive data via VNC clipboard.
This attack demonstrates how an attacker can exfiltrate data by
repeatedly copying information to the clipboard.

Attack Pattern:
- Connects to VNC server through SentinelVNC proxy
- Performs rapid clipboard copy operations
- Sends large amounts of data via clipboard sync
"""

import argparse
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.vnc_client import VNCClient, create_vnc_client
from utils.attack_helpers import generate_sensitive_data, log_attack_step, simulate_human_delay


def simulate_clipboard_exfiltration(
    vnc_host: str,
    vnc_port: int,
    data_size: int = 5000,
    num_operations: int = 10,
    delay_between: float = 0.2
):
    """
    Simulate clipboard-based data exfiltration.
    
    Args:
        vnc_host: VNC server hostname
        vnc_port: VNC server port
        data_size: Size of data to copy per operation (bytes)
        num_operations: Number of clipboard copy operations
        delay_between: Delay between operations (seconds)
    """
    log_attack_step("Starting Clipboard Exfiltration Attack", {
        "target": f"{vnc_host}:{vnc_port}",
        "data_size": f"{data_size} bytes",
        "operations": num_operations
    })
    
    # Generate sensitive data to exfiltrate
    sensitive_data = generate_sensitive_data(data_size)
    
    # Connect to VNC server (through proxy)
    log_attack_step("Connecting to VNC server")
    client = create_vnc_client(vnc_host, vnc_port)
    
    if not client.connect():
        print("ERROR: Failed to connect to VNC server")
        return False
    
    log_attack_step("Connection established")
    
    try:
        # Perform multiple clipboard copy operations
        for i in range(num_operations):
            log_attack_step(f"Clipboard copy operation {i+1}/{num_operations}")
            
            # Simulate clipboard copy by sending data
            # In real VNC, this would be clipboard sync messages
            chunk_size = 1500  # Typical clipboard chunk size
            chunks = data_size // chunk_size
            
            for chunk_idx in range(chunks):
                chunk_data = sensitive_data[chunk_idx*chunk_size:(chunk_idx+1)*chunk_size]
                if not client.simulate_clipboard_copy(chunk_data, repeat=1):
                    print(f"ERROR: Failed to send clipboard data chunk {chunk_idx+1}")
                    return False
                
                time.sleep(0.01)  # Small delay between chunks
            
            # Delay between operations to simulate real attack
            if i < num_operations - 1:
                time.sleep(delay_between)
        
        log_attack_step("Clipboard exfiltration attack completed")
        print("\n[SUCCESS] Attack simulation completed")
        print("Expected Detection: Application Detector should detect 'clipboard_spike_candidate'")
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
        description="Simulate clipboard-based data exfiltration attack"
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
        "--data-size",
        type=int,
        default=5000,
        help="Data size per operation in bytes (default: 5000)"
    )
    parser.add_argument(
        "--operations",
        type=int,
        default=10,
        help="Number of clipboard operations (default: 10)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay between operations in seconds (default: 0.2)"
    )
    
    args = parser.parse_args()
    
    success = simulate_clipboard_exfiltration(
        args.vnc_host,
        args.vnc_port,
        args.data_size,
        args.operations,
        args.delay
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

