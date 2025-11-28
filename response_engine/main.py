import logging
from typing import List, Literal, Dict, Optional

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("response_engine")

app = FastAPI(title="SentinelVNC Response Engine")


# --- Data contracts ---------------------------------------------------------


class DetectorEvent(BaseModel):
    event_id: str
    session_id: str
    timestamp: str
    detector: Literal["network", "app", "visual"]
    type: str
    confidence: float
    details: Dict[str, object] = Field(default_factory=dict)
    artifact_refs: List[str] = Field(default_factory=list)


class Incident(BaseModel):
    incident_id: str
    session_id: str
    risk_score: int
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    events: List[DetectorEvent]
    recommended_action: Literal["allow", "deceive", "kill_session", "deception_mode"]
    artifact_refs: List[str] = Field(default_factory=list)


class ForensicsStartRequest(BaseModel):
    incident_id: str
    session_id: str
    artifact_refs: List[str] = Field(default_factory=list)


# --- Configuration ----------------------------------------------------------


PROXY_CONTROL_URL = "http://localhost:8000/admin/kill-session"
FORENSICS_START_URL = "http://localhost:9100/forensics/start"


# --- Action implementations -------------------------------------------------


async def kill_session(session_id: str) -> None:
    logger.info("[response] kill_session requested for session_id=%s", session_id)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(PROXY_CONTROL_URL, json={"session_id": session_id})
            logger.info(
                "[response] proxy kill_session response status=%s body=%s",
                resp.status_code,
                resp.text,
            )
        except Exception as exc:
            logger.error("[response] failed to call proxy kill_session: %s", exc)


async def activate_deception(session_id: str) -> dict:
    logger.info("[response] activate_deception for session_id=%s", session_id)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                PROXY_CONTROL_URL.replace("kill-session", "activate-deception"),
                json={"session_id": session_id},
            )
            logger.info(
                "[response] proxy activate_deception response status=%s body=%s",
                resp.status_code,
                resp.text,
            )
            if resp.status_code == 200:
                return {"status": "deception_active"}
            return {"status": "error", "detail": resp.text, "code": resp.status_code}
        except Exception as exc:
            logger.error("[response] failed to call proxy activate-deception: %s", exc)
            return {"status": "error", "detail": str(exc)}


async def allow_session(session_id: str) -> None:
    logger.info("[response] allow_session for session_id=%s", session_id)


async def call_forensics_engine(incident: Incident) -> None:
    payload = ForensicsStartRequest(
        incident_id=incident.incident_id,
        session_id=incident.session_id,
        artifact_refs=incident.artifact_refs,
    )
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(FORENSICS_START_URL, json=payload.model_dump())
            logger.info("[response] forensics/start response %s %s", resp.status_code, resp.text)
        except Exception as exc:
            logger.error("[response] failed to call forensics/start: %s", exc)


# --- API endpoints ----------------------------------------------------------


@app.post("/incoming-incident")
async def incoming_incident(incident: Incident):
    logger.info(
        "[response] received incident=%s session_id=%s risk_score=%d action=%s",
        incident.incident_id,
        incident.session_id,
        incident.risk_score,
        incident.recommended_action,
    )

    action = incident.recommended_action

    if action == "allow":
        await allow_session(incident.session_id)
    elif action in ("deceive", "deception_mode"):
        deception_result = await activate_deception(incident.session_id)
        logger.info("[response] deception_result=%s", deception_result)
    elif action == "kill_session":
        await kill_session(incident.session_id)
    else:
        logger.warning("[response] unknown recommended_action=%s", action)

    await call_forensics_engine(incident)

    return {"status": "ok"}
