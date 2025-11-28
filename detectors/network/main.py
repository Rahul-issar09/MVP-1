from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from typing import Literal, List, Dict
import logging
import uuid
import asyncio
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("network_detector")

app = FastAPI(title="SentinelVNC Network Detector")


RISK_ENGINE_URL = "http://localhost:9000/detector-events"


class ProxyEvent(BaseModel):
    session_id: str = Field(..., description="Session identifier from proxy")
    ts: str = Field(..., description="ISO-8601 timestamp from proxy")
    stream: Literal["network_stream"]
    direction: Literal["client_to_server", "server_to_client"]
    type: Literal["raw_chunk"]
    length: int = Field(..., ge=0)


class DetectorEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    timestamp: str
    detector: Literal["network"]
    type: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    details: Dict[str, object] = Field(default_factory=dict)
    artifact_refs: List[str] = Field(default_factory=list)


def build_detector_event(event: ProxyEvent) -> DetectorEvent:
    if event.length > 1500 and event.direction == "client_to_server":
        event_type = "file_transfer_candidate"
        confidence = 0.2
    elif event.length > 0 and event.direction == "client_to_server":
        event_type = "network_activity"
        confidence = 0.05
    else:
        event_type = "server_response_activity"
        confidence = 0.05

    return DetectorEvent(
        session_id=event.session_id,
        timestamp=event.ts,
        detector="network",
        type=event_type,
        confidence=confidence,
        details={
            "length": event.length,
            "direction": event.direction,
        },
    )


async def send_to_risk_engine(detector_event: DetectorEvent) -> None:
    backoff = 0.5
    async with httpx.AsyncClient() as client:
        for attempt in range(3):
            try:
                await client.post(RISK_ENGINE_URL, json=detector_event.model_dump())
                return
            except Exception as exc:
                logger.warning(
                    "Failed to send detector_event to risk_engine (attempt %d): %s",
                    attempt + 1,
                    exc,
                )
                if attempt == 2:
                    break
                await asyncio.sleep(backoff)
                backoff *= 2


@app.post("/events")
async def handle_event(event: ProxyEvent, request: Request):
    client_host = request.client.host if request.client else "unknown"
    logger.info(
        "Received network event from %s: session_id=%s length=%d direction=%s",
        client_host,
        event.session_id,
        event.length,
        event.direction,
    )

    detector_event = build_detector_event(event)
    logger.info("network detector_event: %s", detector_event.model_dump())
    await send_to_risk_engine(detector_event)
    return {"status": "ok", "detector_event": detector_event}
