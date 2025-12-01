# Scenario 6: Steganography Exfiltration Attack

## Overview

This scenario demonstrates how an attacker can hide data in images using steganography and exfiltrate it through VNC, making detection extremely difficult.

## Attack Description

**Attack Vector**: Visual Layer - Steganography  
**Threat Type**: Covert Channel / Data Exfiltration  
**Difficulty**: High  
**Detection Difficulty**: Very High (requires advanced analysis)

## Attack Steps

1. **Attacker gains VNC access**
2. **Attacker embeds data in images** using steganography:
   - Uses tools like Steghide, OpenStego, or custom tools
   - Hides data in LSB (Least Significant Bit) of pixels
   - Creates images with high entropy
3. **Attacker transmits steganographic images** through VNC:
   - Sends images with hidden data
   - May use legitimate-looking images
   - High entropy indicates hidden data
4. **Data is exfiltrated** hidden within image files
5. **Attacker extracts data** from images on local machine

## Attack Simulation

### Run Attack Simulation

```bash
cd scripts/test_bed
python attack_scripts/steganography_exfil.py \
    --vnc-host localhost \
    --vnc-port 5900 \
    --num-images 5 \
    --image-size 5000
```

### Parameters

- `--vnc-host`: VNC server hostname (default: localhost)
- `--vnc-port`: VNC server port (default: 5900)
- `--num-images`: Number of images with hidden data (default: 5)
- `--image-size`: Size of each image in bytes (default: 5000)

## Expected Detection

### Visual Detector

**Event Type**: `steganography_detected`  
**Confidence**: Variable (based on entropy analysis)  
**Details**:
- High entropy detected in images
- LSB analysis indicates steganography
- Suspicious patterns in image data

### Risk Engine

**Risk Score**: Medium to High  
**Risk Level**: MEDIUM or HIGH  
**Recommended Action**: `deceive` or `kill_session`

## Prevention Mechanisms

### 1. Detection (SentinelVNC)

- **Visual Detector**: Analyzes image entropy
- **Steganography Detection**: LSB analysis and entropy checks
- **Pattern Analysis**: Identifies steganographic patterns
- **Risk Engine**: Correlates visual indicators

### 2. Configuration Recommendations

**For VNC Administrators**:
- Monitor image transfers
- Set image transfer limits
- Log all image operations
- Restrict image transfer permissions

**For SentinelVNC**:
- Configure steganography detection thresholds
- Increase weight for `steganography_detected` in risk_weights.yaml
- Enable entropy analysis for all images
- Use advanced steganography detection algorithms

### 3. Best Practices

- **Image Monitoring**: Monitor all image transfers
- **Entropy Analysis**: Analyze image entropy for steganography
- **LSB Analysis**: Check least significant bits for hidden data
- **Response**: Activate deception mode for suspicious images

## Validation

```bash
python validation/check_incidents.py --scenario steganography
```

Expected results:
- Incident with MEDIUM or HIGH risk level
- Visual detector events for steganography
- High entropy indicators present

## Real-World Impact

**Severity**: Critical  
**Likelihood**: Low (requires technical expertise)  
**Data at Risk**: 
- Any data that can be hidden in images
- Credentials and secrets
- Confidential documents
- Command and control data

## Mitigation Summary

| Mitigation | Effectiveness | Implementation |
|------------|---------------|----------------|
| Image monitoring | Medium | VNC logging |
| Entropy analysis | High | SentinelVNC |
| LSB analysis | High | Visual Detector |
| SentinelVNC detection | High | Automatic |
| Deception mode | High | Response Engine |

## Technical Details

**Steganography Tools**:
- Steghide: Hides data in images
- OpenStego: Open-source steganography
- LSB techniques: Least Significant Bit manipulation

**Detection Methods**:
- **Entropy Analysis**: High entropy indicates hidden data
- **LSB Analysis**: Checks least significant bits for patterns
- **Statistical Analysis**: Detects statistical anomalies
- **Visual Analysis**: OCR and pattern recognition

**Detection Challenges**:
- Very difficult to detect without analysis
- Legitimate images can have high entropy
- Requires sophisticated detection algorithms
- May require manual review

## Advanced Detection

SentinelVNC's Visual Detector includes:
- Entropy calculation for images
- LSB ratio analysis
- Statistical pattern detection
- OCR for sensitive text detection

See `detectors/visual/ocr_stego.py` for implementation details.

