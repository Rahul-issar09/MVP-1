# Scenario 3: DNS Tunneling Exfiltration Attack

## Overview

This scenario demonstrates how an attacker can use DNS queries as a covert channel to exfiltrate data, making detection more difficult.

## Attack Description

**Attack Vector**: Network Layer - DNS Protocol Abuse  
**Threat Type**: Covert Channel / Data Exfiltration  
**Difficulty**: Medium  
**Detection Difficulty**: High (requires advanced pattern analysis)

## Attack Steps

1. **Attacker gains VNC access**
2. **Attacker sets up DNS tunnel** (may use tools like dns2tcp, iodine)
3. **Attacker encodes data** in DNS query subdomains
4. **Attacker sends DNS queries** through VNC connection:
   - Small packets (60-120 bytes)
   - High frequency queries
   - Encoded data in query strings
5. **Data is exfiltrated** via DNS responses or query patterns

## Attack Simulation

### Run Attack Simulation

```bash
cd scripts/test_bed
python attack_scripts/dns_tunnel_exfil.py \
    --vnc-host localhost \
    --vnc-port 5900 \
    --num-queries 50 \
    --interval 0.1
```

### Parameters

- `--vnc-host`: VNC server hostname (default: localhost)
- `--vnc-port`: VNC server port (default: 5900)
- `--num-queries`: Number of DNS-like queries (default: 50)
- `--interval`: Interval between queries in seconds (default: 0.1)

## Expected Detection

### Network Detector

**Event Type**: `dns_tunnel_suspected`  
**Confidence**: 0.15 (for packets 60-120 bytes)  
**Details**:
- Small packet sizes (typical DNS query size)
- Sustained pattern of similar-sized packets
- Timing patterns consistent with DNS tunneling

### Risk Engine

**Risk Score**: Medium (may require multiple queries to trigger)  
**Risk Level**: MEDIUM  
**Recommended Action**: `deceive` (deception mode)

## Prevention Mechanisms

### 1. Detection (SentinelVNC)

- **Network Detector**: Analyzes packet sizes and patterns
- **Entropy Analysis**: Detects unusual DNS-like patterns
- **Timing Analysis**: Identifies DNS tunneling timing signatures
- **Risk Engine**: Correlates multiple indicators

### 2. Configuration Recommendations

**For Network Administrators**:
- Monitor DNS query patterns
- Set DNS query rate limits
- Block suspicious DNS domains
- Use DNS filtering and logging

**For SentinelVNC**:
- Lower threshold for DNS tunnel detection
- Increase weight for `dns_tunnel_suspected` in risk_weights.yaml
- Enable deception mode for medium-risk DNS patterns

### 3. Best Practices

- **DNS Monitoring**: Monitor all DNS queries from VNC sessions
- **Rate Limiting**: Limit DNS query frequency
- **Pattern Analysis**: Use ML-based pattern detection
- **Response**: Activate deception mode for suspicious patterns

## Validation

```bash
python validation/check_incidents.py --scenario dns_tunnel
```

Expected results:
- Incident with MEDIUM risk level
- Network detector events for DNS tunnel
- Deception mode activated (if configured)

## Real-World Impact

**Severity**: High  
**Likelihood**: Medium  
**Data at Risk**: 
- Any data that can be encoded in DNS queries
- Small files and credentials
- Command and control communications

## Mitigation Summary

| Mitigation | Effectiveness | Implementation |
|------------|---------------|----------------|
| DNS monitoring | High | Network tools |
| Rate limiting | Medium | DNS server config |
| SentinelVNC detection | Medium | Pattern analysis |
| Deception mode | High | Response Engine |
| DNS filtering | High | Network security |

## Technical Details

**DNS Tunneling Tools**:
- dns2tcp: TCP over DNS
- iodine: IP over DNS
- dnscat2: Command and control over DNS

**Detection Challenges**:
- Small packet sizes blend with normal traffic
- Legitimate DNS queries can hide malicious ones
- Requires statistical analysis over time

