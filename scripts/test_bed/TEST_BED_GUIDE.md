# SentinelVNC Test Bed - Complete Guide

## Introduction

The SentinelVNC Test Bed is a comprehensive system for simulating, demonstrating, and validating VNC-based data exfiltration attacks. It provides:

- **Attack Simulation Scripts**: Automated tools to simulate various exfiltration methods
- **Scenario Documentation**: Detailed step-by-step guides for each attack type
- **Validation Tools**: Scripts to verify detection and response mechanisms
- **Automated Testing**: Test runners for comprehensive validation

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Setup](#setup)
3. [Attack Scenarios](#attack-scenarios)
4. [Running Tests](#running-tests)
5. [Validation](#validation)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Python 3.8+**: For running attack scripts
- **TigerVNC or RealVNC**: VNC server for testing
- **SentinelVNC Services**: All SentinelVNC components running
  - Risk Engine (port 9000)
  - Response Engine (port 9200)
  - Forensics Service (port 9100)
  - Blockchain Gateway (port 8080)
  - Proxy (port 5900 or configured port)

### Network Requirements

- VNC server accessible from test machine
- SentinelVNC proxy intercepting VNC traffic
- All SentinelVNC services on same network or localhost

## Setup

### 1. Initial Setup

```bash
cd scripts/test_bed
./setup_test_environment.sh
```

This script will:
- Check Python installation
- Install required dependencies
- Set up script permissions
- Verify VNC server availability
- Check SentinelVNC services

### 2. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Start SentinelVNC Services

Before running tests, ensure all SentinelVNC services are running:

```bash
# Terminal 1: Risk Engine
cd risk_engine
uvicorn main:app --host 0.0.0.0 --port 9000

# Terminal 2: Response Engine
cd response_engine
uvicorn main:app --host 0.0.0.0 --port 9200

# Terminal 3: Forensics Service
cd forensics
uvicorn main:app --host 0.0.0.0 --port 9100

# Terminal 4: Blockchain Gateway
python -m uvicorn blockchain.gateway:app --host 0.0.0.0 --port 8080

# Terminal 5: Proxy
cd proxy
node index.js
```

### 4. Start VNC Server

```bash
# TigerVNC example
vncserver :1 -geometry 1920x1080

# Or RealVNC
vncserver :1
```

## Attack Scenarios

The test bed includes 6 comprehensive attack scenarios:

### Scenario 1: Clipboard Exfiltration
- **Script**: `attack_scripts/clipboard_exfil.py`
- **Documentation**: `scenarios/SCENARIO_01_CLIPBOARD.md`
- **Attack**: Copying sensitive data via clipboard
- **Detection**: Application Detector → `clipboard_spike_candidate`

### Scenario 2: File Transfer Exfiltration
- **Script**: `attack_scripts/file_transfer_exfil.py`
- **Documentation**: `scenarios/SCENARIO_02_FILE_TRANSFER.md`
- **Attack**: Transferring files through VNC
- **Detection**: Network + App Detectors → `file_transfer_candidate`

### Scenario 3: DNS Tunneling
- **Script**: `attack_scripts/dns_tunnel_exfil.py`
- **Documentation**: `scenarios/SCENARIO_03_DNS_TUNNEL.md`
- **Attack**: Covert channel via DNS queries
- **Detection**: Network Detector → `dns_tunnel_suspected`

### Scenario 4: ICMP Tunneling
- **Script**: `attack_scripts/icmp_tunnel_exfil.py`
- **Documentation**: `scenarios/SCENARIO_04_ICMP_TUNNEL.md`
- **Attack**: Covert channel via ICMP packets
- **Detection**: Network Detector → `icmp_tunnel_suspected`

### Scenario 5: Screenshot Burst
- **Script**: `attack_scripts/screenshot_burst.py`
- **Documentation**: `scenarios/SCENARIO_05_SCREENSHOT_BURST.md`
- **Attack**: Rapid screenshot capture
- **Detection**: Visual Detector → `screenshot_burst_candidate`

### Scenario 6: Steganography
- **Script**: `attack_scripts/steganography_exfil.py`
- **Documentation**: `scenarios/SCENARIO_06_STEGANOGRAPHY.md`
- **Attack**: Hidden data in images
- **Detection**: Visual Detector → `steganography_detected`

## Running Tests

### Run All Scenarios

```bash
./run_all_scenarios.sh
```

This will:
1. Run all 6 attack scenarios in sequence
2. Wait between scenarios for processing
3. Check for detected incidents
4. Provide summary report

### Run Individual Scenario

```bash
# Clipboard exfiltration
python attack_scripts/clipboard_exfil.py \
    --vnc-host localhost \
    --vnc-port 5900 \
    --data-size 5000 \
    --operations 10

# File transfer
python attack_scripts/file_transfer_exfil.py \
    --vnc-host localhost \
    --vnc-port 5900 \
    --file-size 100000 \
    --num-files 3

# DNS tunneling
python attack_scripts/dns_tunnel_exfil.py \
    --vnc-host localhost \
    --vnc-port 5900 \
    --num-queries 50

# ICMP tunneling
python attack_scripts/icmp_tunnel_exfil.py \
    --vnc-host localhost \
    --vnc-port 5900 \
    --num-packets 30

# Screenshot burst
python attack_scripts/screenshot_burst.py \
    --vnc-host localhost \
    --vnc-port 5900 \
    --num-screenshots 20

# Steganography
python attack_scripts/steganography_exfil.py \
    --vnc-host localhost \
    --vnc-port 5900 \
    --num-images 5
```

### Custom Configuration

Set environment variables for custom configuration:

```bash
export VNC_HOST=192.168.1.100
export VNC_PORT=5901
export WAIT_BETWEEN=10

./run_all_scenarios.sh
```

## Validation

### Check Incidents

After running an attack, check if incidents were created:

```bash
# Check all incidents
python validation/check_incidents.py

# Check specific scenario
python validation/check_incidents.py --scenario clipboard

# Wait before checking (for processing delay)
python validation/check_incidents.py --wait 5 --scenario file_transfer

# Validate with exit code
python validation/check_incidents.py --validate --scenario clipboard
```

### Verify Detection System

Comprehensive verification of detection mechanisms:

```bash
# Verify all incidents
python validation/verify_detection.py

# Verify specific incident
python validation/verify_detection.py --incident-id INC-12345
```

### View Incidents in Dashboard

1. Start the dashboard:
   ```bash
   cd dashboard
   npm run dev
   ```

2. Open browser: `http://localhost:3000`

3. View incidents and verify detection

## Understanding Results

### Expected Detection Events

Each scenario should trigger specific detector events:

| Scenario | Detector | Event Type | Confidence |
|----------|----------|------------|------------|
| Clipboard | App | `clipboard_spike_candidate` | 0.2 |
| File Transfer | Network | `file_transfer_candidate` | 0.2 |
| File Transfer | App | `file_transfer_metadata` | 0.18 |
| DNS Tunnel | Network | `dns_tunnel_suspected` | 0.15 |
| ICMP Tunnel | Network | `icmp_tunnel_suspected` | 0.15 |
| Screenshot | Visual | `screenshot_burst_candidate` | 0.2 |
| Steganography | Visual | `steganography_detected` | Variable |

### Risk Score Interpretation

- **0-30**: LOW risk → `allow` action
- **31-70**: MEDIUM risk → `deceive` action
- **71-100**: HIGH risk → `kill_session` action

### Response Actions

- **allow**: Session continues, logged
- **deceive**: Session redirected to honeypot
- **kill_session**: Session terminated immediately

## Troubleshooting

### Issue: Cannot connect to VNC server

**Solution**:
- Verify VNC server is running: `vncserver -list`
- Check firewall rules
- Verify port number: `netstat -an | grep 5900`
- Test connection: `nc -zv localhost 5900`

### Issue: No incidents detected

**Possible causes**:
1. Risk Engine not running
2. Detection thresholds too high
3. Attack pattern not strong enough
4. Proxy not forwarding to detectors

**Solution**:
- Check Risk Engine: `curl http://localhost:9000/incidents`
- Lower detection thresholds in `risk_engine/risk_weights.yaml`
- Increase attack intensity (more operations, larger data)
- Verify proxy is forwarding events to detectors

### Issue: Script execution errors

**Solution**:
- Check Python version: `python3 --version` (need 3.8+)
- Install dependencies: `pip3 install -r requirements.txt`
- Check script permissions: `chmod +x attack_scripts/*.py`
- Verify imports: `python3 -c "import httpx"`

### Issue: Services not responding

**Solution**:
- Check service logs
- Verify ports are not in use: `lsof -i :9000`
- Restart services
- Check firewall rules

## Advanced Usage

### Custom Attack Patterns

Modify attack scripts to create custom attack patterns:

```python
# Example: Custom clipboard attack
from utils.vnc_client import create_vnc_client
from utils.attack_helpers import generate_sensitive_data

client = create_vnc_client("localhost", 5900)
client.connect()

# Custom attack logic
data = generate_sensitive_data(10000)
client.simulate_clipboard_copy(data, repeat=20)

client.disconnect()
```

### Integration with CI/CD

Example GitHub Actions workflow:

```yaml
name: Test Bed Validation

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: |
          pip install -r scripts/test_bed/requirements.txt
      - name: Run test bed
        run: |
          cd scripts/test_bed
          ./run_all_scenarios.sh
      - name: Validate detection
        run: |
          python scripts/test_bed/validation/check_incidents.py --validate
```

## Best Practices

1. **Run tests in isolated environment**: Use dedicated test VNC servers
2. **Monitor service logs**: Watch for errors during testing
3. **Validate after each scenario**: Check incidents immediately
4. **Adjust thresholds**: Tune detection thresholds for your environment
5. **Document custom scenarios**: Add new scenarios as needed

## Support

For issues or questions:
1. Check scenario documentation in `scenarios/`
2. Review service logs
3. Verify configuration files
4. Check SentinelVNC main documentation

## References

- SentinelVNC Architecture: `instructions/SDD_B_Engineering_Style.md`
- Product Requirements: `instructions/PRD.md`
- Risk Engine Configuration: `risk_engine/risk_weights.yaml`
- Detector Implementations: `detectors/`

