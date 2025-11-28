from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from typing import Literal, List, Dict
import logging
import uuid
import asyncio
import httpx
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("visual_detector")

app = FastAPI(title="SentinelVNC Visual Detector")


RISK_ENGINE_URL = "http://localhost:9000/detector-events"


class ProxyEvent(BaseModel):
    session_id: str = Field(..., description="Session identifier from proxy")
    ts: str = Field(..., description="ISO-8601 timestamp from proxy")
    stream: Literal["visual_stream"]
    direction: Literal["client_to_server", "server_to_client"]
    type: Literal["raw_chunk"]
    length: int = Field(..., ge=0)


class DetectorEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    timestamp: str
    detector: Literal["visual"]
    type: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    details: Dict[str, object] = Field(default_factory=dict)
    artifact_refs: List[str] = Field(default_factory=list)


def _ensure_screenshot_dir(session_id: str) -> Path:
    """Ensure local directory for screenshots for this session exists.

    This does not attempt to reconstruct real image bytes; it simply
    persists metadata blobs so the forensics engine can treat them as
    visual artifacts for the session.
    """

    base_dir = Path(__file__).resolve().parent
    screenshots_dir = base_dir / "data" / session_id / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    return screenshots_dir


def _persist_visual_chunk(session_id: str, event: ProxyEvent) -> None:
    """Persist a small placeholder file for the visual chunk.

    For MVP we store a text blob with basic metadata; the forensics
    collector only cares that a file exists and can be hashed.
    """

    if event.length <= 0:
        return

    screenshots_dir = _ensure_screenshot_dir(session_id)
    ts_safe = event.ts.replace(":", "-").replace(".", "-")
    filename = f"visual_{ts_safe}_{event.length}.txt"
    dest = screenshots_dir / filename
    if not dest.exists():
        payload = (
            f"session_id={event.session_id}\n"
            f"timestamp={event.ts}\n"
            f"direction={event.direction}\n"
            f"length={event.length}\n"
        )
        dest.write_text(payload, encoding="utf-8")


def build_detector_event(event: ProxyEvent) -> DetectorEvent:
    if event.length > 2000 and event.direction == "client_to_server":
        event_type = "screenshot_burst_candidate"
        confidence = 0.2
    elif event.length > 0 and event.direction == "client_to_server":
        event_type = "visual_activity"
        confidence = 0.05
    else:
        event_type = "server_response_activity"
        confidence = 0.05

    return DetectorEvent(
        session_id=event.session_id,
        timestamp=event.ts,
        detector="visual",
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
        "Received visual event from %s: session_id=%s length=%d direction=%s",
        client_host,
        event.session_id,
        event.length,
        event.direction,
    )

    # Persist a simple on-disk artifact so forensics can later collect it.
    try:
        _persist_visual_chunk(event.session_id, event)
    except Exception as exc:
        logger.warning("Failed to persist visual chunk for session %s: %s", event.session_id, exc)

    detector_event = build_detector_event(event)
    logger.info("visual detector_event: %s", detector_event.model_dump())
    await send_to_risk_engine(detector_event)
    return {"status": "ok", "detector_event": detector_event}
