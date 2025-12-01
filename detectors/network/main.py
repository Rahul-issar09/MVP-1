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
    # Heuristic DNS/ICMP anomaly detection based only on packet size
    # and direction. The proxy currently does not expose full protocol
    # metadata, so these are best-effort signals for tunneling.

    if event.direction == "client_to_server":
        if event.length > 50000:  # Very large file transfers
            event_type = "file_transfer_candidate"
            confidence = 0.7
        elif event.length > 1500:
            # Large client packets are likely file transfers
            event_type = "file_transfer_candidate"
            confidence = 0.5
        elif 60 <= event.length <= 120:
            # Typical DNS packets are small; a sustained pattern of
            # similarly sized packets can indicate DNS tunneling.
            event_type = "dns_tunnel_suspected"
            confidence = 0.4
        elif 100 <= event.length <= 300:
            # ICMP echo with unusual payload sizes used for tunneling.
            event_type = "icmp_tunnel_suspected"
            confidence = 0.4
        elif event.length > 0:
            event_type = "network_activity"
            confidence = 0.05
        else:
            event_type = "network_activity"
            confidence = 0.01
    else:
        # Server-to-client traffic: still useful for context but lower impact.
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
    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(3):
            try:
                resp = await client.post(
                    RISK_ENGINE_URL, 
                    json=detector_event.model_dump(),
                    timeout=10.0
                )
                if resp.status_code == 200:
                    logger.debug(
                        "Successfully sent detector_event to risk_engine: %s",
                        detector_event.type
                    )
                    return
                else:
                    logger.warning(
                        "Risk engine returned status %d: %s",
                        resp.status_code,
                        resp.text[:200]
                    )
            except httpx.ConnectError as exc:
                logger.warning(
                    "Failed to connect to risk_engine at %s (attempt %d): %s. "
                    "Make sure Risk Engine is running on port 9000.",
                    RISK_ENGINE_URL,
                    attempt + 1,
                    type(exc).__name__
                )
            except httpx.TimeoutException:
                logger.warning(
                    "Timeout sending detector_event to risk_engine (attempt %d). "
                    "Risk Engine may be overloaded.",
                    attempt + 1
                )
            except Exception as exc:
                error_msg = str(exc) if str(exc) else f"{type(exc).__name__}"
                logger.warning(
                    "Failed to send detector_event to risk_engine (attempt %d): %s "
                    "(Error type: %s)",
                    attempt + 1,
                    error_msg,
                    type(exc).__name__
                )
            
            if attempt == 2:
                logger.error(
                    "Failed to send detector_event to risk_engine after 3 attempts. "
                    "Event type: %s, Session: %s",
                    detector_event.type,
                    detector_event.session_id[:8]
                )
                break
            
            await asyncio.sleep(backoff)
            backoff *= 2


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "network_detector"}


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
