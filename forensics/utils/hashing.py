from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Union


PathLike = Union[str, Path]


def compute_sha256(path: PathLike, chunk_size: int = 65536) -> str:
    """Compute SHA-256 hash for a file on disk."""
    p = Path(path)
    h = sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_sha256_bytes(data: bytes) -> str:
    """Compute SHA-256 for a bytes buffer."""
    return sha256(data).hexdigest()
