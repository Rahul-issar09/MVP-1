import asyncio
import uuid
from datetime import datetime, timezone

import httpx


async def main():
    base_url = "http://localhost:9000"  # Risk Engine URL

    session_id = "SID-TEST-1"

    events = [
        {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "detector": "app",
            "type": "clipboard_spike_candidate",
            "confidence": 0.9,
            "details": {"length": 1200},
            "artifact_refs": [],
        },
        {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "detector": "network",
            "type": "file_transfer_candidate",
            "confidence": 0.8,
            "details": {"length": 2000},
            "artifact_refs": [],
        },
        {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "detector": "visual",
            "type": "screenshot_burst_candidate",
            "confidence": 0.7,
            "details": {"length": 2500},
            "artifact_refs": [],
        },
    ]

    async with httpx.AsyncClient() as client:
        for e in events:
            resp = await client.post(f"{base_url}/detector-events", json=e)
            print("Sent event", e["type"], "status", resp.status_code)
            print(resp.json())

        # Fetch all incidents
        resp = await client.get(f"{base_url}/incidents")
        print("Incidents:")
        print(resp.json())


if __name__ == "__main__":
    asyncio.run(main())
