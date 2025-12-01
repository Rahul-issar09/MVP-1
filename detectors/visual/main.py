from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from typing import Literal, List, Dict
import logging
import uuid
import asyncio
import httpx
import sys
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("visual_detector")

# Add current directory to path for imports when running as script
_current_dir = Path(__file__).parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

# Import OCR and Steganography detectors
try:
    from ocr_stego import OCRDetector, StegoDetector
except ImportError:
    # Fallback: try relative import if running as module
    try:
        from .ocr_stego import OCRDetector, StegoDetector
    except ImportError:
        logger.warning("Could not import OCRDetector/StegoDetector. OCR and steganography features will be disabled.")
        # Create dummy classes to prevent errors
        class OCRDetector:
            def process(self, *args, **kwargs):
                return {"detected": False}
        class StegoDetector:
            def process(self, *args, **kwargs):
                return {"suspicious": False}

app = FastAPI(title="SentinelVNC Visual Detector")


RISK_ENGINE_URL = "http://localhost:9000/detector-events"


# Optional, best-effort OCR and steganography detectors. These are used only
# when the persisted artifact is a real image file (png/jpg/etc). For the
# current MVP placeholder text artifacts, these detectors will simply skip.
ocr_detector = OCRDetector()
stego_detector = StegoDetector()


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


def _persist_visual_chunk(session_id: str, event: ProxyEvent) -> Path | None:
    """Persist a small placeholder file for the visual chunk.

    For MVP we store a text blob with basic metadata; the forensics
    collector only cares that a file exists and can be hashed.
    """

    if event.length <= 0:
        return None

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

    return dest


def build_detector_event(event: ProxyEvent) -> DetectorEvent:
    if event.length > 5000 and event.direction == "client_to_server":
        # Very large visual chunks indicate screenshot bursts
        event_type = "screenshot_burst_candidate"
        confidence = 0.6
    elif event.length > 2000 and event.direction == "client_to_server":
        event_type = "screenshot_burst_candidate"
        confidence = 0.5
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
    return {"status": "ok", "service": "visual_detector"}


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

    try:
        artifact_path = _persist_visual_chunk(event.session_id, event)
    except Exception as exc:
        artifact_path = None
        logger.warning("Failed to persist visual chunk for session %s: %s", event.session_id, exc)

    detector_event = build_detector_event(event)

    # Best-effort visual analysis: if we eventually persist real image files
    # instead of placeholder text, run OCR and steganography checks and
    # surface a few summary signals into the detector event. When strong
    # signals are present, promote them to first-class event types so the
    # risk engine can weight them appropriately.
    try:
        if artifact_path is not None and artifact_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}:
            ocr_result = ocr_detector.process(event.session_id, str(artifact_path))
            if ocr_result.get("detected"):
                detector_event.type = "sensitive_text_detected"
                ocr_conf = float(ocr_result.get("confidence") or 0.0)
                # Boost confidence toward the OCR detection confidence
                detector_event.confidence = max(detector_event.confidence, ocr_conf)
                detector_event.details["ocr_detected"] = True
                detector_event.details["ocr_confidence"] = ocr_conf
                detector_event.details["ocr_keywords"] = ocr_result.get("keywords")
                detector_event.details["ocr_patterns"] = ocr_result.get("patterns")
                detector_event.details["ocr_text_preview"] = ocr_result.get("text_preview")

            stego_result = stego_detector.process(event.session_id, str(artifact_path))
            if stego_result.get("suspicious"):
                # If we already detected sensitive text, keep that as the
                # primary type but still surface stego details. Otherwise
                # promote to a dedicated steganography_detected event.
                if detector_event.type != "sensitive_text_detected":
                    detector_event.type = "steganography_detected"
                stego_conf = float(stego_result.get("confidence") or 0.0)
                detector_event.confidence = max(detector_event.confidence, stego_conf)
                detector_event.details["stego_suspected"] = True
                detector_event.details["stego_confidence"] = stego_conf
                detector_event.details["stego_entropy"] = stego_result.get("entropy")
                detector_event.details["stego_entropy_suspicious"] = stego_result.get("entropy_suspicious")
                detector_event.details["stego_lsb_ratio"] = stego_result.get("lsb_ratio")
                detector_event.details["stego_lsb_suspicious"] = stego_result.get("lsb_suspicious")
    except Exception as exc:
        logger.warning("Visual analysis failed for session %s: %s", event.session_id, exc)

    logger.info("visual detector_event: %s", detector_event.model_dump())
    await send_to_risk_engine(detector_event)
    return {"status": "ok", "detector_event": detector_event}
