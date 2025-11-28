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
logger = logging.getLogger("app_detector")

app = FastAPI(title="SentinelVNC Application Detector")


RISK_ENGINE_URL = "http://localhost:9000/detector-events"


class ProxyEvent(BaseModel):
    session_id: str = Field(..., description="Session identifier from proxy")
    ts: str = Field(..., description="ISO-8601 timestamp from proxy")
    stream: Literal["app_stream"]
    direction: Literal["client_to_server", "server_to_client"]
    type: Literal["raw_chunk"]
    length: int = Field(..., ge=0)


class DetectorEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    timestamp: str
    detector: Literal["app"]
    type: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    details: Dict[str, object] = Field(default_factory=dict)
    artifact_refs: List[str] = Field(default_factory=list)


def _ensure_app_dir(session_id: str) -> Path:
    """Ensure local directory for application/clipboard artifacts exists."""

    base_dir = Path(__file__).resolve().parent
    app_dir = base_dir / "data" / session_id
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def _append_clipboard_log(session_id: str, event: ProxyEvent) -> None:
    """Append a simple line describing the event into clipboard.log.

    For MVP we treat all client_to_server app_stream chunks as potential
    clipboard/application activity and log metadata only.
    """

    if event.direction != "client_to_server" or event.length <= 0:
        return

    app_dir = _ensure_app_dir(session_id)
    log_path = app_dir / "clipboard.log"
    ts = event.ts
    line = f"{ts} length={event.length} direction={event.direction}\n"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line)


def build_detector_event(event: ProxyEvent) -> DetectorEvent:
    if event.length > 1000 and event.direction == "client_to_server":
        event_type = "clipboard_spike_candidate"
        confidence = 0.2
    elif event.length > 0 and event.direction == "client_to_server":
        event_type = "app_activity"
        confidence = 0.05
    else:
        event_type = "server_response_activity"
        confidence = 0.05

    return DetectorEvent(
        session_id=event.session_id,
        timestamp=event.ts,
        detector="app",
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
        "Received app event from %s: session_id=%s length=%d direction=%s",
        client_host,
        event.session_id,
        event.length,
        event.direction,
    )

    # Persist a simple clipboard/app artifact for this session.
    try:
        _append_clipboard_log(event.session_id, event)
    except Exception as exc:
        logger.warning("Failed to append clipboard log for session %s: %s", event.session_id, exc)

    detector_event = build_detector_event(event)
    logger.info("app detector_event: %s", detector_event.model_dump())
    await send_to_risk_engine(detector_event)
    return {"status": "ok", "detector_event": detector_event}
