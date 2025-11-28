from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    screenshot = "screenshot"
    clipboard = "clipboard"
    network_meta = "network_meta"
    placeholder = "placeholder"


class ArtifactRef(BaseModel):
    type: ArtifactType
    source: str
    ref: str = Field("last", description="Reference hint like 'last_5', 'last_20', 'last_pcap'")


class ArtifactInfo(BaseModel):
    filename: str
    sha256: str
    size_bytes: int
    type: ArtifactType
    source: str
    source_missing: bool = False


class Manifest(BaseModel):
    manifest_version: str = "1.0"
    schema_version: str = "1.0"
    incident_id: str
    session_id: str
    timestamp: str
    artifact_count: int
    artifacts: List[ArtifactInfo]
    merkle_root: str


class ForensicsStartRequest(BaseModel):
    incident_id: str
    session_id: str
    artifact_refs: List[ArtifactRef]
    meta: Optional[Dict[str, object]] = None


class ForensicsStartResponse(BaseModel):
    incident_id: str
    session_id: str
    artifact_count: int
    merkle_root: str


class AnchorRequest(BaseModel):
    incident_id: str
    merkle_root: str
    timestamp: str


class AnchorResponse(BaseModel):
    status: str
    incident_id: str
    merkle_root: str
