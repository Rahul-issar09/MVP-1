from __future__ import annotations

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger("blockchain.client")


class BlockchainClient:
    """Thin client for anchoring and verifying incident Merkle roots on Hyperledger Fabric.

    This client expects a separate HTTP gateway that talks to a real Fabric network.
    Configure the gateway endpoints via environment variables:

    - FABRIC_ANCHOR_URL: URL for anchoring, e.g. http://fabric-gateway:8080/api/anchor
    - FABRIC_VERIFY_URL: URL for verification, e.g. http://fabric-gateway:8080/api/verify
    - FABRIC_API_KEY: optional API key for the gateway, sent as X-API-Key
    """

    def __init__(self) -> None:
        self.anchor_url = os.getenv("FABRIC_ANCHOR_URL")
        self.verify_url = os.getenv("FABRIC_VERIFY_URL")
        self.api_key = os.getenv("FABRIC_API_KEY")
        self._timeout = 5.0

        if not self.anchor_url or not self.verify_url:
            logger.warning(
                "BlockchainClient initialized without FABRIC_ANCHOR_URL/FABRIC_VERIFY_URL; "
                "anchoring and verification will be no-ops.",
            )

    def _build_headers(self) -> dict:
        headers: dict = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def anchor(self, incident_id: str, merkle_root: str, timestamp: str) -> Optional[str]:
        """Anchor an incident's Merkle root on Fabric and return the transaction id.

        Returns None if the gateway is not configured or the call fails.
        """

        if not self.anchor_url:
            logger.info(
                "BlockchainClient.anchor skipped: FABRIC_ANCHOR_URL not configured for incident_id=%s",
                incident_id,
            )
            return None

        payload = {
            "incident_id": incident_id,
            "merkle_root": merkle_root,
            "timestamp": timestamp,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(self.anchor_url, json=payload, headers=self._build_headers())
            logger.info(
                "BC100 FabricAnchorCalled status=%s body=%s incident_id=%s",
                resp.status_code,
                resp.text,
                incident_id,
            )
            if resp.status_code >= 400:
                return None

            data = resp.json()
            tx_id = data.get("tx_id") or data.get("transaction_id")
            return tx_id
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "BC101 FabricAnchorFailed incident_id=%s error=%s",
                incident_id,
                exc,
            )
            return None

    async def verify(self, incident_id: str, merkle_root: str) -> bool:
        """Verify that the given incident/merkle_root pair is anchored on Fabric.

        Returns False if the gateway is not configured or the call fails.
        """

        if not self.verify_url:
            logger.info(
                "BlockchainClient.verify skipped: FABRIC_VERIFY_URL not configured for incident_id=%s",
                incident_id,
            )
            return False

        payload = {
            "incident_id": incident_id,
            "merkle_root": merkle_root,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(self.verify_url, json=payload, headers=self._build_headers())
            logger.info(
                "BC200 FabricVerifyCalled status=%s body=%s incident_id=%s",
                resp.status_code,
                resp.text,
                incident_id,
            )
            if resp.status_code >= 400:
                return False

            data = resp.json()
            # Accept a few common shapes for flexibility: {valid: bool} or {status: "valid"}
            if isinstance(data, dict):
                if "valid" in data:
                    return bool(data["valid"])
                status = data.get("status")
                if isinstance(status, str) and status.lower() in {"valid", "ok", "anchored"}:
                    return True
            return False
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "BC201 FabricVerifyFailed incident_id=%s error=%s",
                incident_id,
                exc,
            )
            return False
