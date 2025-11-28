# SentinelVNC Forensics Engine

The Forensics Engine bundles evidence (screenshots, clipboard logs, network metadata) for a given
`incident_id` and `session_id`, produces a signed `manifest.json`, and computes a Merkle root for
integrity. In Phase 6 it also exposes a stub endpoint to anchor the Merkle root on a blockchain.

## High-Level Flow

1. **Response Engine** decides to start forensics for an incident.
2. It calls **Forensics Engine** `POST /forensics/start` with `incident_id`, `session_id`, and
   `artifact_refs`.
3. Forensics Engine collects artifacts from detectors / proxy, normalises filenames, computes
   SHA-256 per artifact, and builds `manifest.json` + `merkle_root.txt`.
4. Optionally, a caller invokes `POST /forensics/anchor` to send the Merkle root to the
   **Blockchain stub client** (real chain integration will be added in a later phase).

## Folder Structure

```text
/forensics/
  main.py          # FastAPI app (port 9100)
  service.py       # Business logic for start/anchor
  collector.py     # Artifact collectors + placeholders
  utils/
    hashing.py     # SHA-256 helpers
    merkle.py      # Merkle root computation
    storage.py     # Path helpers (project-root aware)
    schema.py      # Pydantic models
  cli/
    run.py         # Manual forensics run
    verify.py      # Offline verification tool
  data/
    <incident_id>/
      raw/         # Normalised artifacts
      manifest/
        manifest.json
        merkle_root.txt
  tests/
    test_forensics.py
```

Artifacts are always stored under:

```text
/forensics/data/<incident_id>/raw/
/forensics/data/<incident_id>/manifest/
```

## Artifact Collection

Inputs to `/forensics/start`:

```jsonc
{
  "incident_id": "INC-123",
  "session_id": "SID-123",
  "artifact_refs": [
    { "type": "screenshot",   "source": "visual_detector",  "ref": "last_5" },
    { "type": "clipboard",    "source": "app_detector",     "ref": "last_20" },
    { "type": "network_meta", "source": "network_detector", "ref": "last_pcap" }
  ],
  "meta": { "triggered_by": "response_engine", "notes": "optional" }
}
```

Collection rules and source locations:

- **Screenshots** (default `N = 5`)
  - Source: `/detectors/visual/data/<session_id>/screenshots/`
  - If folder missing or empty: create `placeholder_screenshot.png` and mark `source_missing: true`.
- **Clipboard** (default `N = 20` lines from tail)
  - Source: `/detectors/app/data/<session_id>/clipboard.log`
  - If file missing: create `placeholder_clipboard.txt` with a short message and
    `source_missing: true`.
- **Network metadata / PCAP-lite**
  - Source: `/proxy/data/<session_id>/network/`
  - If folder missing or empty: create `placeholder_network.json` with `source_missing: true`.

All artifacts:

- Are copied into `/forensics/data/<incident_id>/raw/`.
- Use lowercased, safe filenames (alphanumeric, `_`, `-`, `.`).
- Have SHA-256 computed using `utils/hashing.py`.
- Are listed in `manifest.json`.

## Manifest & Merkle Root

`manifest.json` schema (simplified):

```jsonc
{
  "manifest_version": "1.0",
  "schema_version": "1.0",
  "incident_id": "INC-123",
  "session_id": "SID-123",
  "timestamp": "2025-11-23T00:00:00Z",
  "artifact_count": 3,
  "artifacts": [
    {
      "filename": "screenshot_1.png",
      "sha256": "<hex>",
      "size_bytes": 12345,
      "type": "screenshot",
      "source": "visual_detector",
      "source_missing": false
    }
  ],
  "merkle_root": "<hex>"
}
```

The Merkle root is computed over the list of artifact hashes using `utils/merkle.py` and stored in
both `manifest.json` and `merkle_root.txt`.

Structured log on completion:

```text
FOR100 ForensicsCaptureCompleted { incident_id, artifact_count, merkle_root }
```

## HTTP API

Run the service (from project root):

```bash
uvicorn forensics.main:app --reload --port 9100
```

### POST /forensics/start

```bash
curl -X POST http://localhost:9100/forensics/start \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-123",
    "session_id": "SID-123",
    "artifact_refs": [
      { "type": "screenshot",   "source": "visual_detector",  "ref": "last_5" },
      { "type": "clipboard",    "source": "app_detector",     "ref": "last_20" },
      { "type": "network_meta", "source": "network_detector", "ref": "last_pcap" }
    ],
    "meta": { "triggered_by": "response_engine" }
  }'
```

Response:

```jsonc
{
  "incident_id": "INC-123",
  "session_id": "SID-123",
  "artifact_count": 3,
  "merkle_root": "<hex>"
}
```

### POST /forensics/anchor

Anchors the Merkle root using the blockchain stub client (Phase 6).

```bash
curl -X POST http://localhost:9100/forensics/anchor \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-123",
    "merkle_root": "<hex>",
    "timestamp": "2025-11-23T00:00:00Z"
  }'
```

Response:

```jsonc
{ "status": "anchored_stub", "incident_id": "INC-123", "merkle_root": "<hex>" }
```

The underlying stub client simply prints:

```text
BLOCKCHAIN_ANCHOR_STUB: { ...payload... }
```

## CLI Usage

From project root:

```bash
python -m forensics.cli.run --incident INC-123 --session SID-123

python -m forensics.cli.verify --incident INC-123
```

- `run` executes the same pipeline as `/forensics/start` but locally.
- `verify` recomputes all hashes and Merkle root from disk and prints PASS/FAIL.

## Future Blockchain Integration (Phase 7+)

In later phases, `blockchain.stub_client.anchor` will be replaced with a real Hyperledger Fabric
client that:

- Submits the `merkle_root` and incident metadata to a smart contract.
- Returns a transaction ID / block reference.
- Allows the dashboard to verify evidence integrity against the chain.
