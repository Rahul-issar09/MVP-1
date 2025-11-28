from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from forensics.main import app
from forensics.utils.hashing import compute_sha256
from forensics.utils.merkle import compute_merkle_root


client = TestClient(app)


def test_hashing_known_vector(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("test", encoding="utf-8")
    assert (
        compute_sha256(f)
        == "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"[:64]
    )


def test_merkle_root_length() -> None:
    hashes = ["a" * 64, "b" * 64, "c" * 64]
    root = compute_merkle_root(hashes)
    assert len(root) == 64


def test_forensics_start_creates_manifest(tmp_path: Path, monkeypatch) -> None:
    # Point DATA_ROOT to temp
    from forensics import utils

    monkeypatch.setattr(utils.storage, "DATA_ROOT", tmp_path)  # type: ignore[attr-defined]

    payload = {
        "incident_id": "INC-123",
        "session_id": "SID-123",
        "artifact_refs": [
            {"type": "screenshot", "source": "visual_detector", "ref": "last_5"},
            {"type": "clipboard", "source": "app_detector", "ref": "last_20"},
            {"type": "network_meta", "source": "network_detector", "ref": "last_pcap"},
        ],
        "meta": {"triggered_by": "response_engine"},
    }

    r = client.post("/forensics/start", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["incident_id"] == "INC-123"

    manifest_dir = tmp_path / "INC-123" / "manifest"
    manifest_path = manifest_dir / "manifest.json"
    assert manifest_path.exists()


def test_anchor_stub(monkeypatch, tmp_path: Path) -> None:
    # Prepare fake manifest + merkle_root
    from forensics.utils.storage import get_incident_manifest_dir, DATA_ROOT

    monkeypatch.setattr("forensics.utils.storage.DATA_ROOT", tmp_path)

    incident_id = "INC-999"
    manifest_dir = get_incident_manifest_dir(incident_id)
    manifest = {
        "manifest_version": "1.0",
        "schema_version": "1.0",
        "incident_id": incident_id,
        "session_id": "SID-X",
        "timestamp": "2025-11-23T00:00:00Z",
        "artifact_count": 0,
        "artifacts": [],
        "merkle_root": "deadbeef",
    }
    (manifest_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (manifest_dir / "merkle_root.txt").write_text("deadbeef", encoding="utf-8")

    payload = {
        "incident_id": incident_id,
        "merkle_root": "deadbeef",
        "timestamp": "2025-11-23T00:00:00Z",
    }
    r = client.post("/forensics/anchor", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "anchored_stub"
    assert data["incident_id"] == incident_id
