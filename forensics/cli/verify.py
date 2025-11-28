from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..utils.hashing import compute_sha256
from ..utils.merkle import compute_merkle_root
from ..utils.storage import DATA_ROOT


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify forensics bundle for an incident")
    parser.add_argument("--incident", required=True, help="Incident ID")
    args = parser.parse_args()

    incident_dir = DATA_ROOT / args.incident
    raw_dir = incident_dir / "raw"
    manifest_dir = incident_dir / "manifest"
    manifest_path = manifest_dir / "manifest.json"

    if not manifest_path.exists():
        print(f"manifest.json not found at {manifest_path}")
        raise SystemExit(1)

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = data.get("artifacts", [])
    hashes = []
    for art in artifacts:
        fname = art["filename"]
        expected = art["sha256"]
        fpath = raw_dir / fname
        if not fpath.exists():
            print(f"Missing artifact: {fpath}")
            raise SystemExit(1)
        actual = compute_sha256(fpath)
        if actual != expected:
            print(f"Hash mismatch for {fname}\n expected={expected}\n actual={actual}")
            raise SystemExit(1)
        hashes.append(actual)

    root_stored = data.get("merkle_root", "")
    root_computed = compute_merkle_root(hashes)

    if root_stored != root_computed:
        print("Merkle root mismatch")
        print(f" stored={root_stored}")
        print(f" computed={root_computed}")
        raise SystemExit(1)

    print("PASS: forensics bundle verified")
    print(f" incident={data.get('incident_id')}")
    print(f" artifacts={len(artifacts)}")
    print(f" merkle_root={root_computed}")


if __name__ == "__main__":  # pragma: no cover
    main()
