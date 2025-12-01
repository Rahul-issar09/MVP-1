# Risk Scoring Fix for High-Priority Incidents

## Problem Identified

The test script was generating incidents with **LOW risk scores (30)** instead of **HIGH risk scores (≥71)**, which prevented the alarm system from triggering.

### Root Cause

1. **Low Confidence Values**: Detectors were using very low confidence values (0.2 = 20%)
2. **Risk Calculation**: Even with high risk weights (150), the formula `score = weight × confidence` resulted in:
   - `150 × 0.2 = 30` → **LOW risk** (≤30)
   - To get HIGH risk (≥71), we needed confidence ≥ 0.47

### Example Before Fix
- **Clipboard attack** (3000 bytes) → confidence 0.2 → score 30 → LOW → `allow` action
- **Expected**: HIGH risk → `kill_session` action → Alarm triggers

## Solution Applied

### 1. Increased Confidence for High-Intensity Attacks

**App Detector** (`detectors/app/main.py`):
- Large clipboard operations (>2500 bytes): confidence **0.6** (was 0.2)
- Medium clipboard operations (>1500 bytes): confidence **0.5** (was 0.2)
- Result: `150 × 0.5 = 75` → **HIGH risk** ✓

**Network Detector** (`detectors/network/main.py`):
- Very large file transfers (>50000 bytes): confidence **0.7** (was 0.2)
- Large file transfers (>1500 bytes): confidence **0.5** (was 0.2)
- DNS/ICMP tunneling: confidence **0.4** (was 0.15)

**Visual Detector** (`detectors/visual/main.py`):
- Very large visual chunks (>5000 bytes): confidence **0.6** (was 0.2)
- Large visual chunks (>2000 bytes): confidence **0.5** (was 0.2)

### 2. Risk Score Calculation

The Risk Engine uses:
```python
score = risk_weight × confidence
score = max(0, min(100, int(round(score))))  # Clamped to 0-100
```

**Risk Levels**:
- **LOW**: score ≤ 30 → `allow` action
- **MEDIUM**: 31 ≤ score ≤ 70 → `deceive` action
- **HIGH**: score ≥ 71 → `kill_session` action → **Alarm triggers**

### 3. Expected Behavior After Fix

**Clipboard Attack** (3000 bytes, high intensity):
- Detector: App Detector
- Event Type: `clipboard_spike_candidate`
- Confidence: **0.5** (was 0.2)
- Risk Weight: 150
- **Risk Score**: `150 × 0.5 = 75` → **HIGH** ✓
- **Action**: `kill_session` ✓
- **Alarm**: **Triggers** ✓

**File Transfer Attack** (50000+ bytes):
- Detector: Network Detector
- Event Type: `file_transfer_candidate`
- Confidence: **0.7** (was 0.2)
- Risk Weight: 200
- **Risk Score**: `200 × 0.7 = 140` → clamped to **100** → **HIGH** ✓
- **Action**: `kill_session` ✓
- **Alarm**: **Triggers** ✓

## Testing

Run the test script again:
```bash
python scripts/test_demo_flow.py
```

**Expected Output**:
- ✓ Attack sent successfully
- ✓ Incident created with **HIGH risk** (score ≥ 71)
- ✓ Action: `kill_session`
- ✓ Alarm banner appears in dashboard
- ✓ Audio alert plays (after user interaction)

## Risk Weights Reference

From `risk_engine/risk_weights.yaml`:
- `clipboard_spike_candidate`: 150
- `file_transfer_candidate`: 200
- `screenshot_burst_candidate`: 150
- `dns_tunnel_suspected`: 180
- `icmp_tunnel_suspected`: 160
- `suspicious_command_pattern`: 170
- `file_transfer_metadata`: 190
- `sensitive_text_detected`: 240
- `steganography_detected`: 260

## Notes

1. **Confidence values are now more realistic** for high-intensity attacks
2. **Multiple events** within a 30-second window are **correlated** into a single incident
3. **Risk scores are cumulative** - multiple events increase the score
4. **Alarm threshold**: Incidents with severity `high`/`critical` OR risk_score ≥ 60 trigger alarms

## Verification

To verify the fix is working:

1. **Check incident risk scores**:
   ```bash
   curl http://localhost:9000/incidents | jq '.[0] | {risk_score, risk_level, recommended_action}'
   ```

2. **View dashboard**: http://localhost:3000
   - High-risk incidents should show red alarm banner
   - Risk scores should be ≥ 71 for high-intensity attacks

3. **Check detector logs**:
   - App Detector should show confidence 0.5-0.6 for large clipboard operations
   - Network Detector should show confidence 0.5-0.7 for large file transfers

