# Response Engine

Executes `allow` / `deceive` / `kill_session` actions based on incidents from the Risk Engine.

## API

- `POST /incoming-incident`
  - Accepts an `Incident` JSON as defined in the SDD.
  - Uses `recommended_action` to decide what to do:
    - `allow` → logs and returns `{ "status": "ok" }`.
    - `deceive` / `deception_mode` → calls proxy admin `/admin/activate-deception`.
    - `kill_session` → calls proxy admin `/admin/kill-session`.
  - Always calls the Forensics Engine at `POST http://localhost:9100/forensics/start` with
    `{ incident_id, session_id, artifact_refs }`.

## Deception mode

When `recommended_action` is `deceive` or `deception_mode`:

1. `activate_deception(session_id)` is invoked.
2. The Response Engine calls the proxy admin endpoint:
   - `POST http://localhost:8000/admin/activate-deception`
   - Body: `{ "session_id": "<id>" }`
3. On success the function returns `{ "status": "deception_active" }` and logs the result.

## Kill session

When `recommended_action` is `kill_session`:

1. `kill_session(session_id)` is invoked.
2. The Response Engine calls the proxy admin endpoint:
   - `POST http://localhost:8000/admin/kill-session`
   - Body: `{ "session_id": "<id>" }`
3. Proxy closes both client and upstream sockets and returns `{ "status": "terminated" }`.

## Testing deception mode

1. Start proxy with admin API and honeypot configured:

   ```bash
   # PowerShell
   $env:PROXY_LISTEN_PORT="5900"
   $env:UPSTREAM_HOST="127.0.0.1"
   $env:UPSTREAM_PORT="5901"
   $env:PROXY_ADMIN_PORT="8000"
   $env:HONEYPOT_HOST="127.0.0.1"
   $env:HONEYPOT_PORT="5902"  # separate honeypot VNC server
   node proxy/index.js
   ```

2. Start the Response Engine:

   ```bash
   cd response_engine
   pip install -r requirements.txt
   uvicorn response_engine.main:app --reload --port 9200
   ```

3. Establish a VNC session through the proxy and note the `sessionId` from proxy logs.

4. Send a test incident with `recommended_action="deception_mode"`:

   ```bash
   curl -X POST http://localhost:9200/incoming-incident ^
     -H "Content-Type: application/json" ^
     -d "{
       \"incident_id\": \"INC-DECEPTION-1\",
       \"session_id\": \"<PUT_SESSION_ID_HERE>\",
       \"risk_score\": 60,
       \"risk_level\": \"MEDIUM\",
       \"recommended_action\": \"deception_mode\",
       \"artifact_refs\": [],
       \"events\": []
     }"
   ```

5. The proxy should log:

   - `Session <id>: switched to honeypot ...`
   - `Deception mode enabled for session <id>.`

After that point, all traffic for that session is routed to the honeypot VNC server.

