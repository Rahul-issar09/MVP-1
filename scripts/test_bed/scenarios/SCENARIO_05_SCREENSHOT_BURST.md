# Scenario 5: Screenshot Burst Exfiltration Attack

## Overview

This scenario demonstrates how an attacker can rapidly capture screenshots to exfiltrate visual information, including sensitive data displayed on screen.

## Attack Description

**Attack Vector**: Visual Layer - Screenshot Capture  
**Threat Type**: Data Exfiltration  
**Difficulty**: Low  
**Detection Difficulty**: Medium (requires pattern analysis)

## Attack Steps

1. **Attacker gains VNC access**
2. **Attacker identifies sensitive visual data** on screen
3. **Attacker performs rapid screenshot capture**:
   - Captures screenshots in quick succession
   - Captures multiple screens/windows
   - Focuses on areas with sensitive information
4. **Screenshots are transmitted** through VNC connection
5. **Attacker receives visual data** on local machine

## Attack Simulation

### Run Attack Simulation

```bash
cd scripts/test_bed
python attack_scripts/screenshot_burst.py \
    --vnc-host localhost \
    --vnc-port 5900 \
    --num-screenshots 20 \
    --screenshot-size 3000 \
    --interval 0.05
```

### Parameters

- `--vnc-host`: VNC server hostname (default: localhost)
- `--vnc-port`: VNC server port (default: 5900)
- `--num-screenshots`: Number of screenshots (default: 20)
- `--screenshot-size`: Size of each screenshot in bytes (default: 3000)
- `--interval`: Interval between screenshots in seconds (default: 0.05)

## Expected Detection

### Visual Detector

**Event Type**: `screenshot_burst_candidate`  
**Confidence**: 0.2 (for large chunks >2000 bytes)  
**Details**:
- Large visual data chunks detected
- Rapid screenshot capture pattern
- Burst behavior indicates potential exfiltration

### Risk Engine

**Risk Score**: Medium to High  
**Risk Level**: MEDIUM or HIGH  
**Recommended Action**: `deceive` or `kill_session`

## Prevention Mechanisms

### 1. Detection (SentinelVNC)

- **Visual Detector**: Monitors screenshot capture patterns
- **Burst Detection**: Identifies rapid screenshot sequences
- **Risk Engine**: Correlates visual activity with other indicators
- **Response Engine**: Automatically responds based on risk

### 2. Configuration Recommendations

**For VNC Administrators**:
- Set screenshot rate limits
- Monitor screenshot capture frequency
- Log all screenshot operations
- Restrict screenshot permissions

**For SentinelVNC**:
- Configure screenshot burst detection thresholds
- Increase weight for `screenshot_burst_candidate` in risk_weights.yaml
- Enable automatic response for screenshot bursts

### 3. Best Practices

- **Rate Limiting**: Limit screenshot capture frequency
- **Monitoring**: Real-time monitoring of screenshot activity
- **Response**: Automatic blocking of excessive screenshots
- **Forensics**: Capture screenshot logs for investigation

## Validation

```bash
python validation/check_incidents.py --scenario screenshot_burst
```

Expected results:
- Incident with MEDIUM or HIGH risk level
- Visual detector events for screenshot burst
- Response action triggered

## Real-World Impact

**Severity**: High  
**Likelihood**: Medium  
**Data at Risk**: 
- Information displayed on screen
- Passwords and credentials (if visible)
- Documents and files (if open)
- Application interfaces
- Any visual information

## Mitigation Summary

| Mitigation | Effectiveness | Implementation |
|------------|---------------|----------------|
| Rate limiting | High | VNC configuration |
| Screenshot monitoring | High | SentinelVNC |
| SentinelVNC detection | High | Automatic |
| Session termination | High | Response Engine |
| User awareness | Medium | Training |

## Technical Details

**Screenshot Tools**:
- VNC built-in screenshot
- Screen capture utilities
- Automated screenshot scripts

**Detection Challenges**:
- Screenshots may be legitimate
- Requires pattern analysis over time
- Burst detection needs threshold tuning

