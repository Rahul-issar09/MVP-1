from __future__ import annotations

from typing import Any, Dict


def anchor(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Stub blockchain anchor client.

    Phase 6: just log/print payload and return a stub response.
    In a later phase this will call a real Hyperledger Fabric backend.
    """

    print("BLOCKCHAIN_ANCHOR_STUB:", payload)
    return {"status": "ok_stub", "tx": None}
