# Proxy Gateway

Transparent VNC interception and session splitter into network_stream, app_stream, visual_stream. Emits events per SDD data contracts.

## Admin HTTP API

The proxy exposes an admin API on `PROXY_ADMIN_PORT` (default `8000`).

### Kill session

- `POST /admin/kill-session`
- Body:

  ```json
  { "session_id": "<uuid>" }
  ```

- Behaviour:
  - Finds the active TCP session with that `session_id`.
  - Destroys client and upstream sockets.
  - Logs: `Session <id> terminated via Response Engine.`
  - Returns:

    ```json
    { "status": "terminated" }
    ```

### Activate deception mode

- `POST /admin/activate-deception`
- Body:

  ```json
  { "session_id": "<uuid>" }
  ```

- Behaviour:
  - Switches the upstream for the session to a honeypot VNC server.
  - Sets an internal `deception=true` flag for that session.
  - Logs: `Deception mode enabled for session <id>.`
  - Returns:

    ```json
    { "status": "deception_active" }
    ```

## Honeypot configuration

Configure where deception-mode sessions are routed using environment variables:

- `HONEYPOT_HOST` (default: `UPSTREAM_HOST`)
- `HONEYPOT_PORT` (default: `UPSTREAM_PORT`)

Example (PowerShell):

```bash
$env:PROXY_LISTEN_PORT="5900"
$env:UPSTREAM_HOST="127.0.0.1"
$env:UPSTREAM_PORT="5901"      # real VNC server
$env:HONEYPOT_HOST="127.0.0.1" # honeypot VNC server
$env:HONEYPOT_PORT="5902"
$env:PROXY_ADMIN_PORT="8000"
node proxy/index.js
```

