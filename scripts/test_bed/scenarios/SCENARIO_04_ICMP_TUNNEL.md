# Scenario 4: ICMP Tunneling Exfiltration Attack

## Overview

This scenario demonstrates how an attacker can use ICMP (ping) packets as a covert channel to exfiltrate data, similar to DNS tunneling but using ICMP protocol.

## Attack Description

**Attack Vector**: Network Layer - ICMP Protocol Abuse  
**Threat Type**: Covert Channel / Data Exfiltration  
**Difficulty**: Medium  
**Detection Difficulty**: High (ICMP is often allowed through firewalls)

## Attack Steps

1. **Attacker gains VNC access**
2. **Attacker sets up ICMP tunnel** (may use tools like ptunnel, icmpsh)
3. **Attacker encodes data** in ICMP packet payloads
4. **Attacker sends ICMP packets** through VNC connection:
   - Medium-sized packets (100-300 bytes)
   - Regular intervals
   - Encoded data in payloads
5. **Data is exfiltrated** via ICMP echo requests/replies

## Attack Simulation

### Run Attack Simulation

```bash
cd scripts/test_bed
python attack_scripts/icmp_tunnel_exfil.py \
    --vnc-host localhost \
    --vnc-port 5900 \
    --num-packets 30 \
    --interval 0.1
```

### Parameters

- `--vnc-host`: VNC server hostname (default: localhost)
- `--vnc-port`: VNC server port (default: 5900)
- `--num-packets`: Number of ICMP-like packets (default: 30)
- `--interval`: Interval between packets in seconds (default: 0.1)

## Expected Detection

### Network Detector

**Event Type**: `icmp_tunnel_suspected`  
**Confidence**: 0.15 (for packets 100-300 bytes)  
**Details**:
- Medium packet sizes (typical ICMP tunnel size)
- Sustained pattern of similar-sized packets
- Timing patterns consistent with ICMP tunneling

### Risk Engine

**Risk Score**: Medium  
**Risk Level**: MEDIUM  
**Recommended Action**: `deceive` (deception mode)

## Prevention Mechanisms

### 1. Detection (SentinelVNC)

- **Network Detector**: Analyzes packet sizes and patterns
- **Pattern Analysis**: Detects ICMP tunneling signatures
- **Timing Analysis**: Identifies ICMP tunnel timing patterns
- **Risk Engine**: Correlates indicators

### 2. Configuration Recommendations

**For Network Administrators**:
- Monitor ICMP traffic patterns
- Set ICMP rate limits
- Block ICMP from untrusted sources
- Log all ICMP traffic

**For SentinelVNC**:
- Configure ICMP tunnel detection thresholds
- Increase weight for `icmp_tunnel_suspected` in risk_weights.yaml
- Enable deception mode for suspicious ICMP patterns

### 3. Best Practices

- **ICMP Monitoring**: Monitor ICMP traffic from VNC sessions
- **Rate Limiting**: Limit ICMP packet frequency
- **Firewall Rules**: Restrict ICMP to necessary traffic only
- **Response**: Activate deception mode for suspicious patterns

## Validation

```bash
python validation/check_incidents.py --scenario icmp_tunnel
```

Expected results:
- Incident with MEDIUM risk level
- Network detector events for ICMP tunnel
- Deception mode activated

## Real-World Impact

**Severity**: High  
**Likelihood**: Medium  
**Data at Risk**: 
- Any data that can be encoded in ICMP payloads
- Small files and credentials
- Command and control communications

## Mitigation Summary

| Mitigation | Effectiveness | Implementation |
|------------|---------------|----------------|
| ICMP monitoring | High | Network tools |
| Rate limiting | Medium | Firewall config |
| SentinelVNC detection | Medium | Pattern analysis |
| Deception mode | High | Response Engine |
| ICMP filtering | High | Firewall rules |

## Technical Details

**ICMP Tunneling Tools**:
- ptunnel: TCP over ICMP
- icmpsh: Shell over ICMP
- Hans: IP over ICMP

**Detection Challenges**:
- ICMP is often allowed through firewalls
- Normal ping traffic can hide malicious traffic
- Requires payload analysis

