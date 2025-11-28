from __future__ import annotations

import io
import logging
import re
from pathlib import Path
from typing import Iterable, List, Tuple

from .utils.hashing import compute_sha256, compute_sha256_bytes
from .utils.merkle import compute_merkle_root
from .utils.schema import ArtifactInfo, ArtifactRef, ArtifactType
from .utils.storage import (
    DATA_ROOT,
    get_app_clipboard_path,
    get_incident_manifest_dir,
    get_incident_raw_dir,
    get_network_meta_dir,
    get_visual_screenshots_dir,
)

logger = logging.getLogger("forensics.collector")


SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9_.-]+")


def _safe_name(name: str) -> str:
    name = name.strip().lower()
    return SAFE_NAME_RE.sub("_", name)


class ForensicsCollector:
    """Collects artifacts for a given incident/session into the forensics data root."""

    def __init__(self) -> None:
        DATA_ROOT.mkdir(parents=True, exist_ok=True)

    # ---- public API -----------------------------------------------------

    def run_collection(
        self,
        incident_id: str,
        session_id: str,
        refs: Iterable[ArtifactRef],
    ) -> Tuple[List[ArtifactInfo], str]:
        raw_dir = get_incident_raw_dir(incident_id)
        artifacts: List[ArtifactInfo] = []

        for ref in refs:
            if ref.type is ArtifactType.screenshot:
                artifacts.extend(self._collect_screenshots(incident_id, session_id, ref, raw_dir))
            elif ref.type is ArtifactType.clipboard:
                artifacts.extend(self._collect_clipboard(incident_id, session_id, ref, raw_dir))
            elif ref.type is ArtifactType.network_meta:
                artifacts.extend(self._collect_network_meta(incident_id, session_id, ref, raw_dir))

        hashes = [a.sha256 for a in artifacts]
        merkle_root = compute_merkle_root(hashes)
        return artifacts, merkle_root

    # ---- helpers --------------------------------------------------------

    def _collect_screenshots(
        self,
        incident_id: str,
        session_id: str,
        ref: ArtifactRef,
        raw_dir: Path,
    ) -> List[ArtifactInfo]:
        src_dir = get_visual_screenshots_dir(session_id)
        n = self._parse_last_n(ref.ref, default=5)

        if not src_dir.exists() or not any(src_dir.iterdir()):
            logger.warning("Screenshot source missing for session %s at %s", session_id, src_dir)
            return [self._create_placeholder_bytes(
                raw_dir,
                filename="placeholder_screenshot.png",
                content=b"placeholder screenshot",
                type_=ArtifactType.screenshot,
                source=ref.source,
                source_missing=True,
            )]

        files = sorted([p for p in src_dir.iterdir() if p.is_file()])[-n:]
        artifacts: List[ArtifactInfo] = []
        for idx, src in enumerate(files, start=1):
            dest_name = _safe_name(f"screenshot_{idx}{src.suffix}")
            dest = raw_dir / dest_name
            dest.write_bytes(src.read_bytes())
            sha = compute_sha256(dest)
            artifacts.append(
                ArtifactInfo(
                    filename=dest_name,
                    sha256=sha,
                    size_bytes=dest.stat().st_size,
                    type=ArtifactType.screenshot,
                    source=ref.source,
                    source_missing=False,
                )
            )
        return artifacts

    def _collect_clipboard(
        self,
        incident_id: str,
        session_id: str,
        ref: ArtifactRef,
        raw_dir: Path,
    ) -> List[ArtifactInfo]:
        src_file = get_app_clipboard_path(session_id)
        n = self._parse_last_n(ref.ref, default=20)

        if not src_file.exists():
            logger.warning("Clipboard source missing for session %s at %s", session_id, src_file)
            return [self._create_placeholder_bytes(
                raw_dir,
                filename="placeholder_clipboard.txt",
                content=b"clipboard source missing",
                type_=ArtifactType.clipboard,
                source=ref.source,
                source_missing=True,
            )]

        lines = src_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        tail = "\n".join(lines[-n:]) + "\n" if lines else ""
        dest_name = _safe_name("clipboard_tail.txt")
        dest = raw_dir / dest_name
        dest.write_text(tail, encoding="utf-8")
        sha = compute_sha256(dest)
        return [
            ArtifactInfo(
                filename=dest_name,
                sha256=sha,
                size_bytes=dest.stat().st_size,
                type=ArtifactType.clipboard,
                source=ref.source,
                source_missing=False,
            )
        ]

    def _collect_network_meta(
        self,
        incident_id: str,
        session_id: str,
        ref: ArtifactRef,
        raw_dir: Path,
    ) -> List[ArtifactInfo]:
        src_dir = get_network_meta_dir(session_id)

        if not src_dir.exists() or not any(src_dir.iterdir()):
            logger.warning("Network meta source missing for session %s at %s", session_id, src_dir)
            return [self._create_placeholder_bytes(
                raw_dir,
                filename="placeholder_network.json",
                content=b"network meta source missing",
                type_=ArtifactType.network_meta,
                source=ref.source,
                source_missing=True,
            )]

        # For now: take all files in the directory as network artifacts
        artifacts: List[ArtifactInfo] = []
        for idx, src in enumerate(sorted(src_dir.iterdir()), start=1):
            if not src.is_file():
                continue
            dest_name = _safe_name(f"network_{idx}{src.suffix}")
            dest = raw_dir / dest_name
            dest.write_bytes(src.read_bytes())
            sha = compute_sha256(dest)
            artifacts.append(
                ArtifactInfo(
                    filename=dest_name,
                    sha256=sha,
                    size_bytes=dest.stat().st_size,
                    type=ArtifactType.network_meta,
                    source=ref.source,
                    source_missing=False,
                )
            )
        if not artifacts:
            return [self._create_placeholder_bytes(
                raw_dir,
                filename="placeholder_network.json",
                content=b"network meta empty",
                type_=ArtifactType.network_meta,
                source=ref.source,
                source_missing=True,
            )]
        return artifacts

    # ---- small utilities ------------------------------------------------

    @staticmethod
    def _parse_last_n(ref: str, default: int) -> int:
        # ref like "last_5"; if not parsable, return default
        try:
            if ref.startswith("last_"):
                return int(ref.split("_", 1)[1])
        except Exception:
            pass
        return default

    def _create_placeholder_bytes(
        self,
        raw_dir: Path,
        filename: str,
        content: bytes,
        type_: ArtifactType,
        source: str,
        source_missing: bool,
    ) -> ArtifactInfo:
        dest_name = _safe_name(filename)
        dest = raw_dir / dest_name
        dest.write_bytes(content)
        sha = compute_sha256(dest)
        return ArtifactInfo(
            filename=dest_name,
            sha256=sha,
            size_bytes=dest.stat().st_size,
            type=type_,
            source=source,
            source_missing=source_missing,
        )
