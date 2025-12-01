# SentinelVNC – Project Completion Plan

This document is a **step-by-step plan** to take SentinelVNC from the current MVP-level implementation to a **complete product** matching the PRD and [tasks.md](cci:7://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/instructions/tasks.md:0:0-0:0).

It assumes the current status:

- Proxy, Network/App/Visual Detectors, Risk Engine, Response Engine, and Forensics are implemented and wired together.
- Visual OCR + Stego are integrated.
- Forensics bundles artifacts and computes a Merkle root.
- Blockchain is a stub.
- Dashboard is mostly missing.
- Some detection rules and security/deployment polish are still pending.

---

## Phase 0 – Prerequisites & Overview

1. **Read the key design docs**
   - [instructions/PRD.md](cci:7://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/instructions/PRD.md:0:0-0:0)
   - [instructions/SDD_B_Engineering_Style.md](cci:7://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/instructions/SDD_B_Engineering_Style.md:0:0-0:0)
   - [instructions/tasks.md](cci:7://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/instructions/tasks.md:0:0-0:0)

2. **Understand current components**
   - `proxy/`
   - `detectors/network`, `detectors/app`, `detectors/visual`
   - `risk_engine/`
   - `response_engine/`
   - `forensics/`
   - `blockchain/` (stub)
   - `dashboard/` (skeleton or empty)

3. **Verify basic MVP flow still works**
   - Start all services.
   - Run a sample VNC session.
   - Confirm: events → incident → response (kill/deceive) → forensics bundle.

Only after this, move on to the completion plan below.

---

## Phase 1 – Finish Detection Rules (Network, App, Visual)

### 1.1 Network Detector: DNS/ICMP + Entropy

**Goal:** Implement the remaining detection items from [tasks.md](cci:7://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/instructions/tasks.md:0:0-0:0) / PRD.

**Steps:**

1. Open [detectors/network/main.py](cci:7://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/detectors/network/main.py:0:0-0:0).
2. Add logic to:
   - Detect **DNS tunneling** patterns:
     - Many small TXT queries.
     - Very long, high‑entropy domain labels.
   - Detect **ICMP tunneling**:
     - Suspicious ICMP payload sizes and frequencies.
3. Emit **new event types**, for example:
   - `dns_tunnel_suspected`
   - `icmp_tunnel_suspected`
4. Update [risk_engine/risk_weights.yaml](cci:7://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/risk_engine/risk_weights.yaml:0:0-0:0):
   - Add weights for these new event types (medium-high).

### 1.2 App Detector: Suspicious Commands & File Transfer Metadata

**Goal:** Cover all Application Detector bullets in [tasks.md](cci:7://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/instructions/tasks.md:0:0-0:0).

**Steps:**

1. Open [detectors/app/main.py](cci:7://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/detectors/app/main.py:0:0-0:0).
2. Extend parsing of app/terminal events to:
   - Match **suspicious command patterns**, e.g.:
     - `scp`, `rsync`, `curl` / `wget` to external IPs.
     - `powershell -enc`, base64 blobs.
     - `nc`, `ssh` to unknown hosts.
   - When matched, emit `suspicious_command_pattern` events.
3. For **file-transfer metadata**:
   - Detect signs like file chooser dialogs, known upload paths, or app logs.
   - Emit a `file_transfer_metadata` event type.
4. Update [risk_engine/risk_weights.yaml](cci:7://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/risk_engine/risk_weights.yaml:0:0-0:0) with sensible weights.

### 1.3 Visual Detector: Promote OCR/Stego Findings

**Goal:** Make OCR + Stego first-class signals in risk scoring.

**Steps:**

1. Open [detectors/visual/ocr_stego.py](cci:7://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/detectors/visual/ocr_stego.py:0:0-0:0) and [detectors/visual/main.py](cci:7://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/detectors/visual/main.py:0:0-0:0).
2. When OCR finds sensitive content (passwords, keys, PII):
   - Create [DetectorEvent](cci:2://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/detectors/visual/main.py:37:0-45:58) with `type="sensitive_text_detected"`.
3. When Stego detector flags suspicious entropy/LSB:
   - Create [DetectorEvent](cci:2://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/detectors/visual/main.py:37:0-45:58) with `type="steganography_detected"`.
4. Ensure `details` still contain text, bounding boxes, entropy values.
5. Update [risk_engine/risk_weights.yaml](cci:7://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/risk_engine/risk_weights.yaml:0:0-0:0) to add:
   - `sensitive_text_detected`
   - `steganography_detected`
   with high weights.

---

## Phase 2 – Correlator & Risk Engine Hardening

### 2.1 Finalize Risk Policy

**Goal:** Map risk levels to actions clearly as per PRD.

**Steps:**

1. Open [risk_engine/main.py](cci:7://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/risk_engine/main.py:0:0-0:0).
2. Ensure the mapping function (e.g. [action_from_risk_level](cci:1://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/risk_engine/main.py:113:0-118:25)) is:

   - `LOW`    → `allow`
   - `MEDIUM` → `deceive`
   - `HIGH`   → [kill_session](cci:1://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/response_engine/main.py:53:0-64:81)

3. Document this mapping in comments and in the root README.

### 2.2 Risk Explanation Support

**Goal:** Support dashboard/analyst “explainability”.

**Steps:**

1. In [risk_engine/main.py](cci:7://file:///c:/Users/rahul/OneDrive/Desktop/SIH%20Winner/risk_engine/main.py:0:0-0:0), add a helper that:
   - Sums risk contribution by `event.type`.
   - Produces a simple explanation object, e.g.:

   ```json
   {
     "total_score": 85,
     "top_contributors": [
       {"type": "sensitive_text_detected", "score": 50},
       {"type": "clipboard_spike_candidate", "score": 35}
     ]
   }

   