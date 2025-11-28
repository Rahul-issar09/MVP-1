from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FORENSICS_ROOT = PROJECT_ROOT / "forensics"
DATA_ROOT = FORENSICS_ROOT / "data"


def get_incident_raw_dir(incident_id: str) -> Path:
    d = DATA_ROOT / incident_id / "raw"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_incident_manifest_dir(incident_id: str) -> Path:
    d = DATA_ROOT / incident_id / "manifest"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_visual_screenshots_dir(session_id: str) -> Path:
    return PROJECT_ROOT / "detectors" / "visual" / "data" / session_id / "screenshots"


def get_app_clipboard_path(session_id: str) -> Path:
    return PROJECT_ROOT / "detectors" / "app" / "data" / session_id / "clipboard.log"


def get_network_meta_dir(session_id: str) -> Path:
    return PROJECT_ROOT / "proxy" / "data" / session_id / "network"
