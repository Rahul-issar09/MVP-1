1. Problem

VNC remote access technologies (TigerVNC, RealVNC) are vulnerable to data exfiltration via:

Clipboard copying

File transfers

Screenshots

Script-driven exfiltration

DNS/ICMP covert channels

Visual steganography

Organizations have no real-time detection or prevention mechanism for such attacks.

2. Goals / Non-Goals
2.1 Goals

Detect all forms of VNC-based data exfiltration

Real-time multi-stream analysis (network + app + visual)

Assign risk score to every session

Automatically enforce response: kill, isolate, deceive

Provide forensic evidence

Anchor incident hashes on blockchain

Provide analyst dashboard + explainable alerts

2.2 Non-Goals

Monitoring RDP, SSH, TeamViewer

Monitoring non-VNC protocols

Full OS-level forensics

Mobile VNC client monitoring

3. High-Level Architecture
User → SentinelVNC Proxy → (Network Stream / App Stream / Visual Stream)
      → Detectors → Event Bus → Correlator → Risk Engine
      → Response Engine → Forensics → Blockchain → Dashboard

4. Component Design
4.1 Proxy Gateway

Transparent VNC interception

Assign session_id

Split traffic into:

network_stream

app_stream

visual_stream

Forward original session to actual VNC server

4.2 Network Detector
Responsibilities

Detect:

File transfers

DNS tunneling

ICMP covert channels

Entropy anomalies

Clipboard sync over network

Algorithms

Signature rules

Flow-based anomaly detection

Entropy calculation

Timing analysis

Outputs → network_event JSON.

4.3 Application Detector
Responsibilities

Detect:

Clipboard spikes

Copy-paste abuse

File-transfer metadata

Suspicious keystrokes

Script-driven exfil

Outputs → app_event JSON.

4.4 Visual Detector
Responsibilities

Detect:

Sensitive text (OCR)

Steganography signals

Screenshot bursts

Rapid page changes

Outputs → visual_event JSON.

4.5 Event Bus

Receives all detector events

Guarantees ordering

Forwards to correlator

4.6 Correlator

Aggregate events by session_id and time window

Build an event timeline

4.7 Risk Engine

Assigns risk score (0–100)

Risk levels:

Low = 0–30

Medium = 31–70

High = 71+

4.8 Response Engine

Low → Allow & log

Medium → Deception mode

High → Kill session + isolate

Logs all responses

4.9 Forensics Engine

Create evidence bundle

Store:

PCAP

Screenshots

Clipboard logs

manifest.json

Compute SHA-256 and Merkle root

4.10 Blockchain Layer

Store only:

incident_hash

timestamp

incident_id

Ensures immutability

4.11 Analyst Dashboard & Explainable AI

Evidence viewer

Timeline

Risk explanations

Blockchain verification

Export forensic PDF

5. Data Contracts
5.1 Detector Event
{
  "event_id": "GUID",
  "session_id": "SID01",
  "timestamp": "...",
  "detector": "network|app|visual",
  "type": "clipboard_spike|dns_tunnel|sensitive_text",
  "confidence": 0.92,
  "details": {},
  "artifact_refs": []
}

5.2 Incident
{
  "incident_id": "INC001",
  "session_id": "SID01",
  "risk_score": 87,
  "risk_level": "HIGH",
  "events": [],
  "recommended_action": "kill_session",
  "artifact_refs": []
}

6. Security

No sensitive data on-chain

Encryption everywhere

Secure evidence store

Role-based access

Tamper-proof auditing

7. Scalability

All detectors horizontally scalable

Stateless services

Event bus partitioning

Proxy cluster support

8. Failure Handling

Proxy fails open with logging

Detector failover logic

Event retry queue

Graceful recoveries

9. Appendix

Architecture Diagram

Risk Scoring Table

Detector Thresholds