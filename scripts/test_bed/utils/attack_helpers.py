"""
Helper functions for attack simulations.
"""

import time
import random
import string
from typing import List, Optional


def generate_sensitive_data(size: int = 1024) -> str:
    """Generate mock sensitive data (passwords, credit cards, etc.)."""
    patterns = [
        "Password: secret123",
        "Credit Card: 4532-1234-5678-9010",
        "SSN: 123-45-6789",
        "API Key: sk_live_abc123xyz",
        "Database: user=admin, pass=password",
    ]
    
    data = []
    while len('\n'.join(data)) < size:
        data.append(random.choice(patterns))
    
    return '\n'.join(data)[:size]


def generate_large_text(size: int = 10000) -> str:
    """Generate large text for clipboard/file transfer simulation."""
    chars = string.ascii_letters + string.digits + string.punctuation + ' \n'
    return ''.join(random.choice(chars) for _ in range(size))


def simulate_human_delay(min_ms: int = 100, max_ms: int = 500):
    """Simulate human-like delays between actions."""
    delay = random.uniform(min_ms / 1000.0, max_ms / 1000.0)
    time.sleep(delay)


def create_file_content(size: int, pattern: Optional[str] = None) -> bytes:
    """Create file content for transfer simulation."""
    if pattern:
        content = pattern.encode('utf-8')
        return (content * (size // len(content)) + content[:size % len(content)])
    else:
        return generate_large_text(size).encode('utf-8')


def log_attack_step(step: str, details: Optional[dict] = None):
    """Log an attack step for documentation."""
    print(f"[ATTACK] {step}")
    if details:
        for key, value in details.items():
            print(f"  {key}: {value}")

