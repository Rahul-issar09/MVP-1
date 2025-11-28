# WINDSURF BUILD TASKS — SENTINELVNC

## MASTER GOAL
Build the full SentinelVNC product using SDD_B_Engineering_Style.md and PRD.md.

---

## Phase 1 — Project Structure
- Create monorepo:
  /proxy
  /detectors/network
  /detectors/app
  /detectors/visual
  /risk_engine
  /response_engine
  /forensics
  /blockchain
  /dashboard
  /shared
  /scripts
- Configure environment files + README.

---

## Phase 2 — Proxy Gateway
- Implement VNC transparent proxy.
- Assign session_id.
- Split traffic:
  - network_stream
  - app_stream
  - visual_stream
- Output must match SDD data contracts.

---

## Phase 3 — Detection Engine

### Network Detector
- Packet parser  
- File-transfer signature detection  
- DNS/ICMP anomaly detection  
- Entropy analysis  

### Application Detector
- Clipboard spike detection  
- File-transfer metadata analysis  
- Suspicious command pattern detection  

### Visual Detector
- OCR for sensitive text  
- Steganography entropy  
- Screenshot burst detection  

All detectors must output `detector_event`.

---

## Phase 4 — Correlator & Risk Engine
- Merge detector events  
- Build session-level timeline  
- Compute risk score  
- Output incident schema as defined in SDD  

---

## Phase 5 — Response Engine
- Allow / deceive / kill  
- Integrate with proxy for kill_session  
- Log response actions  

---

## Phase 6 — Forensics & Blockchain
- Bundle artifacts  
- Generate manifest.json  
- Compute merkle_root  
- Store hash on Hyperledger Fabric  

---

## Phase 7 — Dashboard
- Incident list  
- Incident detail view  
- Evidence viewer  
- Risk explanation  
- Blockchain verification  

---

## Phase 8 — Integration
- Connect proxy → detectors → event bus → risk → response → forensics → blockchain → dashboard  
- Perform integration tests  

---

## Phase 9 — Polish & Deployment
- Optimize performance  
- Write documentation  
- Add deployment scripts  

---
