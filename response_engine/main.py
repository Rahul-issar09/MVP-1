import logging
import os
from typing import List, Literal, Dict, Optional

import httpx
from fastapi import FastAPI, Header, HTTPException
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
    artifact_refs: List = Field(default_factory=list)  # Empty list - forensics will use defaults based on session_id


# --- Configuration ----------------------------------------------------------


# Proxy admin port - can be configured via environment variable
# Default is 8000, but if proxy isn't running, response engine will log warning
PROXY_ADMIN_PORT = os.getenv("PROXY_ADMIN_PORT", "8000")
PROXY_CONTROL_URL = f"http://localhost:{PROXY_ADMIN_PORT}/admin/kill-session"
FORENSICS_START_URL = "http://localhost:9100/forensics/start"

# Simple API key configuration for internal service-to-service calls and
# protecting incoming admin-style endpoints.
RESPONSE_ENGINE_API_KEY = os.getenv("RESPONSE_ENGINE_API_KEY")
PROXY_ADMIN_API_KEY = os.getenv("PROXY_ADMIN_API_KEY")
FORENSICS_API_KEY = os.getenv("FORENSICS_API_KEY")


# --- Action implementations -------------------------------------------------


async def kill_session(session_id: str) -> None:
    logger.info("[response] kill_session requested for session_id=%s", session_id)
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            headers = {}
            if PROXY_ADMIN_API_KEY:
                headers["X-API-Key"] = PROXY_ADMIN_API_KEY
            resp = await client.post(PROXY_CONTROL_URL, json={"session_id": session_id}, headers=headers)
            if resp.status_code == 200:
                logger.info("[response] Session %s terminated successfully", session_id)
            elif resp.status_code == 404:
                logger.warning(
                    "[response] Proxy admin endpoint not found (404). "
                    "Proxy may not be running or admin port is different. "
                    "This is OK for demo without real VNC sessions."
                )
            else:
                logger.warning(
                    "[response] proxy kill_session response status=%s body=%s",
                    resp.status_code,
                    resp.text,
                )
        except httpx.ConnectError:
            logger.warning(
                "[response] Cannot connect to proxy admin at %s. "
                "Proxy may not be running. This is OK for demo without real VNC sessions.",
                PROXY_CONTROL_URL
            )
        except Exception as exc:
            logger.warning("[response] Failed to call proxy kill_session: %s (This is OK for demo)", exc)


async def activate_deception(session_id: str) -> dict:
    logger.info("[response] activate_deception for session_id=%s", session_id)
    deception_url = PROXY_CONTROL_URL.replace("kill-session", "activate-deception")
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            headers = {}
            if PROXY_ADMIN_API_KEY:
                headers["X-API-Key"] = PROXY_ADMIN_API_KEY
            resp = await client.post(
                deception_url,
                json={"session_id": session_id},
                headers=headers,
            )
            if resp.status_code == 200:
                logger.info("[response] Deception mode activated for session %s", session_id)
                return {"status": "deception_active"}
            elif resp.status_code == 404:
                logger.warning(
                    "[response] Proxy admin endpoint not found (404). "
                    "Proxy may not be running. This is OK for demo without real VNC sessions."
                )
                return {"status": "proxy_unavailable", "note": "Proxy not running - OK for demo"}
            return {"status": "error", "detail": resp.text, "code": resp.status_code}
        except httpx.ConnectError:
            logger.warning(
                "[response] Cannot connect to proxy admin at %s. "
                "Proxy may not be running. This is OK for demo without real VNC sessions.",
                deception_url
            )
            return {"status": "proxy_unavailable", "note": "Proxy not running - OK for demo"}
        except Exception as exc:
            logger.warning("[response] Failed to call proxy activate-deception: %s (This is OK for demo)", exc)
            return {"status": "error", "detail": str(exc)}


async def allow_session(session_id: str) -> None:
    logger.info("[response] allow_session for session_id=%s", session_id)


async def call_forensics_engine(incident: Incident) -> None:
    # Forensics service expects List[ArtifactRef] but will use defaults if empty
    # We pass empty list and let forensics collect based on session_id
    payload = ForensicsStartRequest(
        incident_id=incident.incident_id,
        session_id=incident.session_id,
        artifact_refs=[],  # Empty list - forensics will use defaults
    )
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            headers = {}
            if FORENSICS_API_KEY:
                headers["X-API-Key"] = FORENSICS_API_KEY
            resp = await client.post(FORENSICS_START_URL, json=payload.model_dump(), headers=headers)
            logger.info(
                "[response] forensics/start response status=%s body=%s incident_id=%s session_id=%s",
                resp.status_code,
                resp.text,
                incident.incident_id,
                incident.session_id,
            )
        except Exception as exc:
            logger.error(
                "[response] failed to call forensics/start for incident_id=%s session_id=%s: %s",
                incident.incident_id,
                incident.session_id,
                exc,
            )


# --- API endpoints ----------------------------------------------------------


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "response_engine"}


@app.post("/incoming-incident")
async def incoming_incident(incident: Incident, x_api_key: Optional[str] = Header(default=None)):
    # If an API key is configured, require it for incoming incident traffic
    # from the Risk Engine.
    if RESPONSE_ENGINE_API_KEY and x_api_key != RESPONSE_ENGINE_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid API key")
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
