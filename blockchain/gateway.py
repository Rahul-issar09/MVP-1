from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("blockchain.gateway")

app = FastAPI(title="SentinelVNC Blockchain Gateway (Fallback)", version="1.0.0")

# Add CORS middleware to allow dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnchorPayload(BaseModel):
    incident_id: str
    merkle_root: str
    timestamp: str


class VerifyPayload(BaseModel):
    incident_id: str
    merkle_root: str


DATA_DIR = Path(os.getenv("BLOCKCHAIN_DATA_DIR", "./blockchain_data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
ANCHORS_PATH = DATA_DIR / "anchors.json"

API_KEY = os.getenv("FABRIC_API_KEY")


def _load_anchors() -> Dict[str, Dict[str, str]]:
    if not ANCHORS_PATH.exists():
        return {}
    try:
        return json.loads(ANCHORS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.error("GW001 Failed to load anchors.json: %s", exc)
        return {}


def _save_anchors(data: Dict[str, Dict[str, str]]) -> None:
    try:
        ANCHORS_PATH.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        logger.error("GW002 Failed to save anchors.json: %s", exc)


@app.post("/api/anchor")
async def anchor(
    payload: AnchorPayload,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid API key")

    anchors = _load_anchors()

    tx_id = f"local-{int(time.time()*1000)}-{payload.incident_id}"

    anchors[payload.incident_id] = {
        "merkle_root": payload.merkle_root,
        "timestamp": payload.timestamp,
        "tx_id": tx_id,
    }

    _save_anchors(anchors)

    logger.info(
        "GW100 AnchorStored incident_id=%s merkle_root=%s tx_id=%s",
        payload.incident_id,
        payload.merkle_root,
        tx_id,
    )

    return {"status": "anchored", "tx_id": tx_id}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "blockchain_gateway"}


@app.post("/api/verify")
async def verify(
    payload: VerifyPayload,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid API key")

    anchors = _load_anchors()
    record = anchors.get(payload.incident_id)

    if not record:
        logger.info(
            "GW200 VerifyMiss incident_id=%s reason=no_record",
            payload.incident_id,
        )
        return {"valid": False, "status": "not_found"}

    is_valid = record.get("merkle_root") == payload.merkle_root

    logger.info(
        "GW201 VerifyChecked incident_id=%s merkle_root=%s valid=%s",
        payload.incident_id,
        payload.merkle_root,
        is_valid,
    )

    return {"valid": bool(is_valid), "status": "anchored" if is_valid else "mismatch"}
