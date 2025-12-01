#!/usr/bin/env python3
"""
Steganography Exfiltration Attack Simulation

Simulates an attacker using steganography to hide data in images.
This attack demonstrates how sensitive data can be hidden in visual
content and exfiltrated through VNC.

Attack Pattern:
- Connects to VNC server through SentinelVNC proxy
- Sends image data with high entropy (steganography indicators)
- Simulates visual steganography patterns
"""

import argparse
import sys
import time
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.vnc_client import VNCClient, create_vnc_client
from utils.attack_helpers import log_attack_step


def generate_high_entropy_data(size: int) -> bytes:
    """Generate high-entropy data (typical of steganography)."""
    # High entropy = random data
    return bytes(random.randint(0, 255) for _ in range(size))


def simulate_steganography_exfiltration(
    vnc_host: str,
    vnc_port: int,
    num_images: int = 5,
    image_size: int = 5000
):
    """
    Simulate steganography-based data exfiltration.
    
    Args:
        vnc_host: VNC server hostname
        vnc_port: VNC server port
        num_images: Number of images with hidden data
        image_size: Size of each image data (bytes)
    """
    log_attack_step("Starting Steganography Exfiltration Attack", {
        "target": f"{vnc_host}:{vnc_port}",
        "num_images": num_images,
        "image_size": f"{image_size} bytes"
    })
    
    client = create_vnc_client(vnc_host, vnc_port)
    
    if not client.connect():
        print("ERROR: Failed to connect to VNC server")
        return False
    
    log_attack_step("Connection established")
    
    try:
        log_attack_step(f"Sending {num_images} images with high entropy (steganography indicators)")
        
        for i in range(num_images):
            # Generate high-entropy data (simulates steganography)
            stego_data = generate_high_entropy_data(image_size)
            
            # Send as visual data
            if not client.send_data(stego_data):
                print(f"ERROR: Failed to send steganography data for image {i+1}")
                return False
            
            time.sleep(0.2)  # Delay between images
        
        log_attack_step("Steganography exfiltration attack completed")
        print("\n[SUCCESS] Attack simulation completed")
        print("Expected Detection: Visual Detector should detect 'steganography_detected'")
        print("Expected Detection: High entropy analysis should trigger suspicion")
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
        description="Simulate steganography-based data exfiltration attack"
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
        "--num-images",
        type=int,
        default=5,
        help="Number of images with hidden data (default: 5)"
    )
    parser.add_argument(
        "--image-size",
        type=int,
        default=5000,
        help="Size of each image in bytes (default: 5000)"
    )
    
    args = parser.parse_args()
    
    success = simulate_steganography_exfiltration(
        args.vnc_host,
        args.vnc_port,
        args.num_images,
        args.image_size
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

