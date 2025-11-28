from __future__ import annotations

import argparse
import asyncio

from ..service import ForensicsService
from ..utils.schema import ArtifactRef, ArtifactType, ForensicsStartRequest


def main() -> None:
    parser = argparse.ArgumentParser(description="Manual forensics run (no HTTP)")
    parser.add_argument("--incident", required=True, help="Incident ID")
    parser.add_argument("--session", required=True, help="Session ID")
    args = parser.parse_args()

    service = ForensicsService()

    refs = [
        ArtifactRef(type=ArtifactType.screenshot, source="visual_detector", ref="last_5"),
        ArtifactRef(type=ArtifactType.clipboard, source="app_detector", ref="last_20"),
        ArtifactRef(type=ArtifactType.network_meta, source="network_meta", ref="last_pcap"),
    ]

    payload = ForensicsStartRequest(
        incident_id=args.incident,
        session_id=args.session,
        artifact_refs=refs,
    )

    resp = asyncio.run(service.start_forensics(payload))

    print(f"Incident: {resp.incident_id}")
    print(f"Session: {resp.session_id}")
    print(f"Artifacts: {resp.artifact_count}")
    print(f"Merkle root: {resp.merkle_root}")


if __name__ == "__main__":  # pragma: no cover
    main()
