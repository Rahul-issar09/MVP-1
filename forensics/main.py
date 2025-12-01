from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware

from .service import ForensicsService
from .utils.schema import AnchorRequest, ForensicsStartRequest, ForensicsStartResponse, AnchorResponse


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("forensics")

app = FastAPI(title="SentinelVNC Forensics Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = ForensicsService()

FORENSICS_API_KEY = os.getenv("FORENSICS_API_KEY")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "forensics"}


@app.post("/forensics/start", response_model=ForensicsStartResponse)
async def forensics_start(
    payload: ForensicsStartRequest,
    x_api_key: str | None = Header(default=None),
) -> ForensicsStartResponse:
    if FORENSICS_API_KEY and x_api_key != FORENSICS_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid API key")
    try:
        return await service.start_forensics(payload)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Forensics start failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/forensics/anchor", response_model=AnchorResponse)
async def forensics_anchor(
    payload: AnchorRequest,
    x_api_key: str | None = Header(default=None),
) -> AnchorResponse:
    if FORENSICS_API_KEY and x_api_key != FORENSICS_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid API key")
    try:
        return await service.anchor(payload)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Forensics anchor failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# Uvicorn entrypoint hint:
#   uvicorn forensics.main:app --reload --port 9100
