import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Literal, Optional

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("risk_engine")

app = FastAPI(title="SentinelVNC Correlator & Risk Engine")


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

    incident_id = str(uuid.uuid4())
    incident = Incident(
        incident_id=incident_id,
        session_id=session_id,
        risk_score=risk_score,
        risk_level=risk_level,
        events=windowed_events,
        recommended_action=action,
    )

    INCIDENTS[incident_id] = incident
    publish_incident(incident)
    logger.info("Created incident %s for session %s (score=%d, level=%s)",
                incident_id, session_id, risk_score, risk_level)
    return incident


def publish_incident(incident: Incident) -> None:
    # TODO: integrate with Response Engine and Forensics services via HTTP or event bus
    logger.info("Publishing incident %s to Response/Forensics (stub)", incident.incident_id)


# --- API endpoints ----------------------------------------------------------


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
