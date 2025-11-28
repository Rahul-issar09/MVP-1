from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
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


@app.post("/forensics/start", response_model=ForensicsStartResponse)
async def forensics_start(payload: ForensicsStartRequest) -> ForensicsStartResponse:
    try:
        return await service.start_forensics(payload)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Forensics start failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/forensics/anchor", response_model=AnchorResponse)
async def forensics_anchor(payload: AnchorRequest) -> AnchorResponse:
    try:
        return await service.anchor(payload)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Forensics anchor failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# Uvicorn entrypoint hint:
#   uvicorn forensics.main:app --reload --port 9100
