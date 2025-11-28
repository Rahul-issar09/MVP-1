from __future__ import annotations

from typing import List

from .hashing import compute_sha256_bytes


def compute_merkle_root(hashes: List[str]) -> str:
    """Compute a Merkle root from a list of hex-encoded SHA-256 hashes.

    - If list is empty -> return empty string.
    - If odd number of leaves -> duplicate last.
    - Combine siblings by concatenating their raw hex strings and hashing bytes.
    """

    if not hashes:
        return ""

    level = [h.lower() for h in hashes]

    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])

        next_level: List[str] = []
        for i in range(0, len(level), 2):
            combined_hex = (level[i] + level[i + 1]).encode("utf-8")
            next_level.append(compute_sha256_bytes(combined_hex))
        level = next_level

    return level[0]
