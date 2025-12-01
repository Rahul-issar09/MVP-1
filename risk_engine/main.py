import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Literal, Optional

import httpx
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("risk_engine")

app = FastAPI(title="SentinelVNC Correlator & Risk Engine")

# Add CORS middleware to allow dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Data contracts ---------------------------------------------------------


class DetectorEvent(BaseModel):
    event_id: str
    session_id: str
    timestamp: str
    detector: Literal["network", "app", "visual"]
    type: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    details: Dict[str, object] = Field(default_factory=dict)
    artifact_refs: List[str] = Field(default_factory=list)


class Incident(BaseModel):
    incident_id: str
    session_id: str
    risk_score: int
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    events: List[DetectorEvent]
    recommended_action: Literal["allow", "deceive", "kill_session"]
    artifact_refs: List[str] = Field(default_factory=list)


class IncidentAcknowledgeRequest(BaseModel):
    incident_id: str
    acknowledged_by: Optional[str] = None
    note: Optional[str] = None


# --- Configuration ----------------------------------------------------------


WINDOW_SECONDS = 30

# Where to send incidents once created so that responses & forensics are
# executed. For the MVP we call the Response Engine directly over HTTP.
RESPONSE_ENGINE_URL = "http://localhost:9200/incoming-incident"


def load_risk_weights() -> Dict[str, int]:
    try:
        with open("risk_weights.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return {str(k): int(v) for k, v in data.items()}
    except FileNotFoundError:
        logger.warning("risk_weights.yaml not found, using default weights")
        return {}


RISK_WEIGHTS = load_risk_weights()


# --- In-memory stores -------------------------------------------------------


# session_id -> list of DetectorEvent within recent window
SESSION_EVENTS: Dict[str, List[DetectorEvent]] = {}

# incident_id -> Incident
INCIDENTS: Dict[str, Incident] = {}


# --- Risk scoring & correlation --------------------------------------------


def parse_timestamp(ts: str) -> datetime:
    # Expect ISO-8601; fall back to current UTC if parsing fails
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        # If parsed datetime is naive, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        logger.warning("Failed to parse timestamp %s, using current UTC time", ts)
        return datetime.now(timezone.utc)


def compute_risk_score(events: List[DetectorEvent]) -> int:
    score = 0.0
    for e in events:
        weight = RISK_WEIGHTS.get(e.type, 0)
        score += weight * float(e.confidence)
    # Clamp and cast to int 0-100
    score = max(0, min(100, int(round(score))))
    return score


def risk_level_from_score(score: int) -> str:
    if score <= 30:
        return "LOW"
    if score <= 70:
        return "MEDIUM"
    return "HIGH"


def action_from_risk_level(level: str) -> str:
    """Map risk levels to response actions.

    Policy (aligned with PRD):
    - LOW    -> allow
    - MEDIUM -> deceive
    - HIGH   -> kill_session
    """
    if level == "LOW":
        return "allow"
    if level == "MEDIUM":
        return "deceive"
    return "kill_session"


def correlate_and_create_incident(session_id: str) -> Optional[Incident]:
    events = SESSION_EVENTS.get(session_id, [])
    if not events:
        return None

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(seconds=WINDOW_SECONDS)
    windowed_events = [
        e for e in events if parse_timestamp(e.timestamp) >= window_start
    ]
    SESSION_EVENTS[session_id] = windowed_events

    if not windowed_events:
        return None

    risk_score = compute_risk_score(windowed_events)
    risk_level = risk_level_from_score(risk_score)
    action = action_from_risk_level(risk_level)

    # For the MVP we always request that forensics collect screenshots,
    # clipboard logs, and network metadata for this session.
    # Note: artifact_refs in Incident model is List[str] for simplicity,
    # but ForensicsStartRequest expects List[ArtifactRef] objects.
    # We'll pass empty list and let forensics collect based on session_id.
    artifact_refs = []

    incident_id = str(uuid.uuid4())
    incident = Incident(
        incident_id=incident_id,
        session_id=session_id,
        risk_score=risk_score,
        risk_level=risk_level,
        events=windowed_events,
        recommended_action=action,
        artifact_refs=artifact_refs,
    )

    INCIDENTS[incident_id] = incident
    publish_incident(incident)
    logger.info("Created incident %s for session %s (score=%d, level=%s)",
                incident_id, session_id, risk_score, risk_level)
    return incident


def publish_incident(incident: Incident) -> None:
    """Send the incident to the Response Engine.

    This is a best-effort fire-and-forget HTTP call so that response actions
    (allow/deceive/kill) and forensics collection can be triggered
    automatically when an incident is created.
    """

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(RESPONSE_ENGINE_URL, json=incident.model_dump())
        logger.info(
            "Published incident %s to Response Engine status=%s",
            incident.incident_id,
            resp.status_code,
        )
    except Exception as exc:
        logger.error(
            "Failed to publish incident %s to Response Engine: %s",
            incident.incident_id,
            exc,
        )


# --- API endpoints ----------------------------------------------------------


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "risk_engine"}


@app.post("/detector-events")
async def ingest_detector_event(event: DetectorEvent):
    session_id = event.session_id
    SESSION_EVENTS.setdefault(session_id, []).append(event)

    incident = correlate_and_create_incident(session_id)
    return {"status": "ok", "incident_created": incident is not None,
            "incident": incident}


@app.get("/incidents")
async def list_incidents() -> List[Incident]:
    return list(INCIDENTS.values())


@app.get("/incidents/{incident_id}")
async def get_incident(incident_id: str) -> Incident:
    incident = INCIDENTS.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@app.get("/incidents/{incident_id}/explanation")
async def get_incident_explanation(incident_id: str) -> Dict[str, object]:
    """Return a simple risk explanation for the given incident.

    The explanation distributes the final risk score across event types using
    the same RISK_WEIGHTS that compute_risk_score uses so that dashboards and
    analysts can see which signals contributed most to the incident.
    """

    incident = INCIDENTS.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    events = incident.events
    if not events:
        return {"total_score": 0, "top_contributors": []}

    # Compute raw contributions per type
    raw_contrib: Dict[str, float] = {}
    for e in events:
        weight = RISK_WEIGHTS.get(e.type, 0)
        raw_contrib[e.type] = raw_contrib.get(e.type, 0.0) + weight * float(e.confidence)

    risk_score = compute_risk_score(events)
    total_raw = sum(raw_contrib.values()) or 1.0

    contributors = []
    for etype, raw in raw_contrib.items():
        scaled = int(round(risk_score * (raw / total_raw)))
        contributors.append({"type": etype, "score": scaled})

    # Sort by descending contribution
    contributors.sort(key=lambda x: x["score"], reverse=True)

    return {"total_score": risk_score, "top_contributors": contributors}


@app.post("/incidents/acknowledge")
async def acknowledge_incident(payload: IncidentAcknowledgeRequest):
    incident = INCIDENTS.get(payload.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    logger.info(
        "Incident %s acknowledged by %s note=%s",
        payload.incident_id,
        payload.acknowledged_by or "unknown",
        payload.note or "",
    )
    return {"status": "ok"}
