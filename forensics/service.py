from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from .collector import ForensicsCollector
from .utils.schema import (
    AnchorRequest,
    AnchorResponse,
    ArtifactRef,
    ArtifactType,
    ForensicsStartRequest,
    ForensicsStartResponse,
    Manifest,
)
from .utils.storage import get_incident_manifest_dir

logger = logging.getLogger("forensics.service")


class ForensicsService:
    def __init__(self) -> None:
        self.collector = ForensicsCollector()

    async def start_forensics(self, payload: ForensicsStartRequest) -> ForensicsStartResponse:
        # If no explicit artifact refs were provided, collect all core types
        # for this session by default.
        refs: List[ArtifactRef]
        if payload.artifact_refs:
            refs = payload.artifact_refs
        else:
            refs = [
                ArtifactRef(type=ArtifactType.screenshot, source="visual_detector", ref="last_5"),
                ArtifactRef(type=ArtifactType.clipboard, source="app_detector", ref="last_20"),
                ArtifactRef(type=ArtifactType.network_meta, source="network_meta", ref="last_pcap"),
            ]

        artifacts, merkle_root = self.collector.run_collection(
            incident_id=payload.incident_id,
            session_id=payload.session_id,
            refs=refs,
        )

        manifest_dir = get_incident_manifest_dir(payload.incident_id)
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        manifest = Manifest(
            incident_id=payload.incident_id,
            session_id=payload.session_id,
            timestamp=timestamp,
            artifact_count=len(artifacts),
            artifacts=artifacts,
            merkle_root=merkle_root,
        )

        manifest_path = manifest_dir / "manifest.json"
        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

        merkle_path = manifest_dir / "merkle_root.txt"
        merkle_path.write_text(merkle_root, encoding="utf-8")

        logger.info(
            "FOR100 ForensicsCaptureCompleted",
            extra={
                "incident_id": payload.incident_id,
                "artifact_count": len(artifacts),
                "merkle_root": merkle_root,
            },
        )

        return ForensicsStartResponse(
            incident_id=payload.incident_id,
            session_id=payload.session_id,
            artifact_count=len(artifacts),
            merkle_root=merkle_root,
        )

    async def anchor(self, payload: AnchorRequest) -> AnchorResponse:
        manifest_dir = get_incident_manifest_dir(payload.incident_id)
        manifest_path = manifest_dir / "manifest.json"
        merkle_path = manifest_dir / "merkle_root.txt"

        if not manifest_path.exists() or not merkle_path.exists():
            raise FileNotFoundError("Manifest or merkle_root not found for incident")

        from json import loads

        manifest_data = loads(manifest_path.read_text(encoding="utf-8"))
        stored_root = merkle_path.read_text(encoding="utf-8").strip()

        if manifest_data.get("merkle_root") != payload.merkle_root or stored_root != payload.merkle_root:
            raise ValueError("Provided merkle_root does not match stored manifest")

        # Call blockchain stub (Phase 6: stub only)
        from blockchain.stub_client import anchor as blockchain_anchor

        result = blockchain_anchor(
            {
                "incident_id": payload.incident_id,
                "merkle_root": payload.merkle_root,
                "timestamp": payload.timestamp,
            }
        )
        logger.info("FOR200 ForensicsAnchorCompleted", extra={"incident_id": payload.incident_id, "result": result})

        return AnchorResponse(
            status="anchored_stub",
            incident_id=payload.incident_id,
            merkle_root=payload.merkle_root,
        )
