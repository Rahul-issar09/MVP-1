# Scenario 2: File Transfer Exfiltration Attack

## Overview

This scenario demonstrates how an attacker can exfiltrate files by transferring them through VNC file transfer mechanisms.

## Attack Description

**Attack Vector**: Network Layer - File Transfer  
**Threat Type**: Data Exfiltration  
**Difficulty**: Low  
**Detection Difficulty**: Low (large data transfers are easily detected)

## Attack Steps

1. **Attacker gains VNC access**
2. **Attacker identifies target files** on remote system
3. **Attacker initiates file transfer**:
   - Uses VNC file transfer feature
   - Transfers multiple files
   - Uses large file sizes to maximize data exfiltration
4. **Files are transferred** through VNC connection
5. **Attacker receives files** on local machine

## Attack Simulation

### Run Attack Simulation

```bash
cd scripts/test_bed
python attack_scripts/file_transfer_exfil.py \
    --vnc-host localhost \
    --vnc-port 5900 \
    --file-size 100000 \
    --chunk-size 4096 \
    --num-files 3
```

### Parameters

- `--vnc-host`: VNC server hostname (default: localhost)
- `--vnc-port`: VNC server port (default: 5900)
- `--file-size`: Size of each file in bytes (default: 100000 = 100KB)
- `--chunk-size`: Transfer chunk size (default: 4096)
- `--num-files`: Number of files to transfer (default: 3)

## Expected Detection

### Network Detector

**Event Type**: `file_transfer_candidate`  
**Confidence**: 0.2 (for packets >1500 bytes)  
**Details**:
- Large packet sizes detected
- Sustained data transfer pattern
- File transfer characteristics

### Application Detector

**Event Type**: `file_transfer_metadata`  
**Confidence**: 0.18 (for packets 800-1500 bytes)  
**Details**:
- File transfer metadata detected
- Transfer operation patterns

### Risk Engine

**Risk Score**: High (typically 60-90)  
**Risk Level**: HIGH  
**Recommended Action**: `kill_session`

## Prevention Mechanisms

### 1. Detection (SentinelVNC)

- **Network Detector**: Monitors packet sizes and patterns
- **Application Detector**: Analyzes file transfer metadata
- **Risk Engine**: Correlates multiple indicators
- **Response Engine**: Automatically terminates high-risk sessions

### 2. Configuration Recommendations

**For VNC Administrators**:
- Disable file transfer feature if not required
- Set file size limits
- Require explicit approval for file transfers
- Log all file transfer operations

**For SentinelVNC**:
- Configure lower threshold for file transfer detection
- Increase weight for `file_transfer_candidate` in risk_weights.yaml
- Enable immediate session termination for file transfers

### 3. Best Practices

- **Access Control**: Restrict file transfer permissions
- **Monitoring**: Real-time monitoring of file transfers
- **Response**: Automatic blocking of unauthorized transfers
- **Forensics**: Capture file transfer logs and metadata

## Validation

```bash
python validation/check_incidents.py --scenario file_transfer
```

Expected results:
- Incident with HIGH risk level
- Network and Application detector events
- Session terminated automatically

## Real-World Impact

**Severity**: Critical  
**Likelihood**: High  
**Data at Risk**: 
- Confidential documents
- Database files
- Source code
- Configuration files
- Any file on the system

## Mitigation Summary

| Mitigation | Effectiveness | Implementation |
|------------|---------------|----------------|
| Disable file transfer | High | VNC configuration |
| File size limits | Medium | VNC server settings |
| SentinelVNC detection | High | Automatic |
| Session termination | High | Response Engine |
| Access control | High | VNC permissions |

