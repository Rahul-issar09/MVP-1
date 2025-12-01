#!/usr/bin/env python3
"""
File Transfer Exfiltration Attack Simulation

Simulates an attacker transferring files through VNC.
This attack demonstrates how large files can be exfiltrated
via VNC file transfer mechanisms.

Attack Pattern:
- Connects to VNC server through SentinelVNC proxy
- Sends large data chunks simulating file transfers
- Uses patterns typical of file transfer operations
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.vnc_client import VNCClient, create_vnc_client
from utils.attack_helpers import log_attack_step


def simulate_file_transfer_exfiltration(
    vnc_host: str,
    vnc_port: int,
    file_size: int = 100000,  # 100KB
    chunk_size: int = 4096,
    num_files: int = 3
):
    """
    Simulate file transfer-based data exfiltration.
    
    Args:
        vnc_host: VNC server hostname
        vnc_port: VNC server port
        file_size: Size of each file in bytes
        chunk_size: Size of each transfer chunk
        num_files: Number of files to transfer
    """
    log_attack_step("Starting File Transfer Exfiltration Attack", {
        "target": f"{vnc_host}:{vnc_port}",
        "file_size": f"{file_size} bytes ({file_size/1024:.1f} KB)",
        "num_files": num_files,
        "chunk_size": chunk_size
    })
    
    client = create_vnc_client(vnc_host, vnc_port)
    
    if not client.connect():
        print("ERROR: Failed to connect to VNC server")
        return False
    
    log_attack_step("Connection established")
    
    try:
        for file_num in range(num_files):
            log_attack_step(f"Transferring file {file_num+1}/{num_files}")
            
            # Simulate file transfer
            if not client.simulate_file_transfer(file_size, chunk_size):
                print(f"ERROR: Failed to transfer file {file_num+1}")
                return False
            
            # Delay between files
            if file_num < num_files - 1:
                time.sleep(0.5)
        
        log_attack_step("File transfer exfiltration attack completed")
        print("\n[SUCCESS] Attack simulation completed")
        print("Expected Detection: Network Detector should detect 'file_transfer_candidate'")
        print("Expected Detection: Application Detector should detect 'file_transfer_metadata'")
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
        description="Simulate file transfer-based data exfiltration attack"
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
        "--file-size",
        type=int,
        default=100000,
        help="File size in bytes (default: 100000 = 100KB)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=4096,
        help="Transfer chunk size in bytes (default: 4096)"
    )
    parser.add_argument(
        "--num-files",
        type=int,
        default=3,
        help="Number of files to transfer (default: 3)"
    )
    
    args = parser.parse_args()
    
    success = simulate_file_transfer_exfiltration(
        args.vnc_host,
        args.vnc_port,
        args.file_size,
        args.chunk_size,
        args.num_files
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

