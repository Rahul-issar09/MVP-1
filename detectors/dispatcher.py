"""
SentinelVNC Detector Dispatcher

Routes proxy events to appropriate detectors based on stream type.
This allows the proxy to send all events to a single endpoint,
which then distributes them to the correct detector service.
"""

from fastapi import FastAPI, Request
from pydantic import BaseModel
import httpx
import logging
from typing import Literal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dispatcher")

app = FastAPI(title="SentinelVNC Detector Dispatcher")

# Detector endpoints
NETWORK_DETECTOR = "http://localhost:8001/events"
APP_DETECTOR = "http://localhost:8002/events"
VISUAL_DETECTOR = "http://localhost:8003/events"


class ProxyEvent(BaseModel):
    session_id: str
    ts: str
    stream: Literal["network_stream", "app_stream", "visual_stream"]
    direction: Literal["client_to_server", "server_to_client"]
    type: Literal["raw_chunk"]
    length: int


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "dispatcher"}


@app.post("/events")
async def dispatch_event(event: ProxyEvent):
    """Route events to appropriate detector based on stream type.
    
    Fire-and-forget: Returns immediately after queuing the event to detector.
    This prevents blocking on the full detection chain.
    """
    import asyncio
    
    target = None
    detector_name = None
    
    if event.stream == "network_stream":
        target = NETWORK_DETECTOR
        detector_name = "network"
    elif event.stream == "app_stream":
        target = APP_DETECTOR
        detector_name = "app"
    elif event.stream == "visual_stream":
        target = VISUAL_DETECTOR
        detector_name = "visual"
    
    if target:
        # Fire-and-forget: Don't wait for detector response
        async def forward_to_detector():
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    resp = await client.post(target, json=event.dict(), timeout=10.0)
                    if resp.status_code == 200:
                        logger.debug(
                            f"Routed {event.stream} (session={event.session_id[:8]}, "
                            f"length={event.length}) to {detector_name} detector"
                        )
                    else:
                        logger.warning(
                            f"Failed to route to {detector_name}: HTTP {resp.status_code} - {resp.text[:100]}"
                        )
                except httpx.ConnectError as e:
                    logger.error(
                        f"Detector {detector_name} not available at {target}. "
                        f"Make sure the detector is running. Error: {type(e).__name__}"
                    )
                except httpx.TimeoutException:
                    logger.error(
                        f"Timeout forwarding to {detector_name} at {target}. "
                        f"Detector may be overloaded or not responding."
                    )
                except Exception as e:
                    error_msg = str(e) if str(e) else f"{type(e).__name__}"
                    logger.error(
                        f"Failed to forward to {target}: {error_msg} "
                        f"(Error type: {type(e).__name__})"
                    )
        
        # Start forwarding in background, don't await
        asyncio.create_task(forward_to_detector())
        
        # Return immediately
        return {"status": "ok", "routed_to": detector_name, "target": target}
    
    logger.warning(f"Unknown stream type: {event.stream}")
    return {"status": "ignored", "reason": "unknown stream type"}

