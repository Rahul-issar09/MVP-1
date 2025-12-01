"""
VNC Client utilities for test bed attack simulations.
Provides helper functions to interact with VNC servers.
"""

import socket
import struct
import time
from typing import Optional, Tuple


class VNCClient:
    """Simple VNC client for test bed attack simulations."""
    
    def __init__(self, host: str, port: int = 5900):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to VNC server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to VNC server: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from VNC server."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
    
    def send_data(self, data: bytes) -> bool:
        """Send raw data to VNC server."""
        if not self.connected or not self.socket:
            return False
        try:
            self.socket.sendall(data)
            return True
        except Exception as e:
            print(f"Failed to send data: {e}")
            return False
    
    def send_large_chunk(self, size: int, pattern: bytes = b'X') -> bool:
        """Send a large chunk of data (simulates file transfer or clipboard)."""
        if not self.connected:
            return False
        
        chunk = pattern * (size // len(pattern)) + pattern[:size % len(pattern)]
        return self.send_data(chunk)
    
    def simulate_clipboard_copy(self, data: str, repeat: int = 1) -> bool:
        """Simulate clipboard copy operation."""
        if not self.connected:
            return False
        
        # VNC clipboard format: RFB protocol message
        # For test bed, we send data that mimics clipboard operations
        clipboard_data = data.encode('utf-8')
        
        for _ in range(repeat):
            # Simulate clipboard copy by sending data chunks
            chunk_size = 1024
            for i in range(0, len(clipboard_data), chunk_size):
                chunk = clipboard_data[i:i+chunk_size]
                if not self.send_data(chunk):
                    return False
                time.sleep(0.01)  # Small delay to simulate real behavior
        
        return True
    
    def simulate_file_transfer(self, file_size: int, chunk_size: int = 4096) -> bool:
        """Simulate file transfer by sending large data chunks."""
        if not self.connected:
            return False
        
        # Generate test data
        test_data = b'F' * chunk_size
        
        chunks = file_size // chunk_size
        for i in range(chunks):
            if not self.send_data(test_data):
                return False
            time.sleep(0.05)  # Simulate network delay
        
        # Send remainder
        remainder = file_size % chunk_size
        if remainder > 0:
            if not self.send_data(b'F' * remainder):
                return False
        
        return True
    
    def simulate_dns_tunnel_pattern(self, num_queries: int = 10) -> bool:
        """Simulate DNS tunneling pattern by sending small packets."""
        if not self.connected:
            return False
        
        # DNS tunnel packets are typically 60-120 bytes
        dns_packet = b'D' * 80  # Typical DNS query size
        
        for _ in range(num_queries):
            if not self.send_data(dns_packet):
                return False
            time.sleep(0.1)  # Simulate query intervals
        
        return True
    
    def simulate_icmp_tunnel_pattern(self, num_packets: int = 10) -> bool:
        """Simulate ICMP tunneling pattern."""
        if not self.connected:
            return False
        
        # ICMP tunnel packets are typically 100-300 bytes
        icmp_packet = b'I' * 200
        
        for _ in range(num_packets):
            if not self.send_data(icmp_packet):
                return False
            time.sleep(0.1)
        
        return True
    
    def simulate_screenshot_burst(self, num_screenshots: int = 20) -> bool:
        """Simulate rapid screenshot capture."""
        if not self.connected:
            return False
        
        # Screenshot data is typically large (2000+ bytes)
        screenshot_data = b'S' * 3000
        
        for _ in range(num_screenshots):
            if not self.send_data(screenshot_data):
                return False
            time.sleep(0.05)  # Very rapid capture
        
        return True
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def create_vnc_client(host: str, port: int = 5900) -> VNCClient:
    """Factory function to create a VNC client."""
    return VNCClient(host, port)

