# Network Detector

Detects file transfers, DNS/ICMP anomalies, entropy spikes; outputs `DetectorEvent` objects for the risk engine.

## Event flow

1. SentinelVNC proxy receives VNC traffic and emits `network_stream` events.
2. This service exposes `POST /events` and accepts `ProxyEvent` JSON from the proxy.
3. It parses the event and builds a `DetectorEvent` with `detector="network"`.
4. The `DetectorEvent` is forwarded to the Correlator & Risk Engine at `http://localhost:9000/detector-events`.

## Testing

- Start the risk engine:
  - `cd risk_engine`
  - `pip install -r requirements.txt`
  - `uvicorn risk_engine.main:app --reload --port 9000`
- Start the network detector:
  - `cd detectors`
  - `pip install -r requirements.txt`
  - `uvicorn detectors.network.main:app --reload --port 8001`
- Send a sample event to the network detector `POST /events` using curl or a REST client.
- Check `GET http://localhost:9000/incidents` to see correlated incidents created from `DetectorEvent`s.
