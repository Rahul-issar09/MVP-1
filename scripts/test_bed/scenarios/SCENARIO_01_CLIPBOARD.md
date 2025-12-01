# Scenario 1: Clipboard Exfiltration Attack

## Overview

This scenario demonstrates how an attacker can exfiltrate sensitive data by repeatedly copying information to the clipboard through a VNC session.

## Attack Description

**Attack Vector**: Application Layer - Clipboard Synchronization  
**Threat Type**: Data Exfiltration  
**Difficulty**: Low  
**Detection Difficulty**: Medium (requires pattern analysis)

## Attack Steps

1. **Attacker gains VNC access** (insider threat or compromised credentials)
2. **Attacker identifies sensitive data** on the remote system
3. **Attacker performs rapid clipboard operations**:
   - Selects sensitive text (passwords, credit cards, API keys)
   - Copies to clipboard (Ctrl+C)
   - Repeats multiple times with different data
4. **Data is synchronized** through VNC clipboard sync mechanism
5. **Attacker receives data** on their local machine

## Attack Simulation

### Prerequisites

- VNC server running (TigerVNC or RealVNC)
- SentinelVNC proxy running and monitoring
- Network connectivity

### Run Attack Simulation

```bash
cd scripts/test_bed
python attack_scripts/clipboard_exfil.py \
    --vnc-host localhost \
    --vnc-port 5900 \
    --data-size 5000 \
    --operations 10 \
    --delay 0.2
```

### Parameters

- `--vnc-host`: VNC server hostname (default: localhost)
- `--vnc-port`: VNC server port (default: 5900)
- `--data-size`: Size of data per operation in bytes (default: 5000)
- `--operations`: Number of clipboard operations (default: 10)
- `--delay`: Delay between operations in seconds (default: 0.2)

## Expected Detection

### Application Detector

**Event Type**: `clipboard_spike_candidate`  
**Confidence**: 0.2 (for large chunks >1500 bytes)  
**Details**:
- Large clipboard data chunks detected
- Multiple rapid clipboard operations
- Pattern indicates potential exfiltration

### Risk Engine

**Risk Score**: Medium to High (depends on number of operations)  
**Risk Level**: MEDIUM or HIGH  
**Recommended Action**: `deceive` or `kill_session`

## Prevention Mechanisms

### 1. Detection (SentinelVNC)

- **Application Detector**: Monitors clipboard sync patterns
- **Risk Engine**: Correlates multiple clipboard spikes
- **Response Engine**: Automatically responds based on risk level

### 2. Configuration Recommendations

**For VNC Administrators**:
- Disable clipboard synchronization if not required
- Configure VNC to log clipboard operations
- Set rate limits on clipboard operations

**For SentinelVNC**:
- Adjust `risk_weights.yaml` to increase weight for `clipboard_spike_candidate`
- Configure lower threshold for clipboard spike detection
- Enable automatic session termination for high-risk clipboard activity

### 3. Best Practices

- **Principle of Least Privilege**: Limit VNC access to necessary users only
- **Monitoring**: Enable real-time monitoring of clipboard operations
- **Response**: Configure automatic response for suspicious patterns
- **Forensics**: Ensure clipboard logs are captured for investigation

## Validation

After running the attack, validate detection:

```bash
python validation/check_incidents.py --scenario clipboard
```

Expected results:
- At least one incident created
- Risk score > 30
- Application detector events present
- Response action triggered (if risk is high)

## Real-World Impact

**Severity**: High  
**Likelihood**: Medium  
**Data at Risk**: 
- Passwords and credentials
- Credit card numbers
- API keys and tokens
- Personal information
- Confidential documents

## Mitigation Summary

| Mitigation | Effectiveness | Implementation |
|------------|---------------|----------------|
| Disable clipboard sync | High | VNC configuration |
| Rate limiting | Medium | VNC server settings |
| SentinelVNC detection | High | Automatic |
| Session termination | High | Response Engine |
| User training | Low | Organizational |

## References

- VNC Clipboard Protocol: RFB Protocol Specification
- SentinelVNC Application Detector: `detectors/app/main.py`
- Risk Engine Configuration: `risk_engine/risk_weights.yaml`

