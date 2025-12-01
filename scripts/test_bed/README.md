# SentinelVNC Test Bed

A comprehensive test bed system for simulating and demonstrating VNC-based data exfiltration attacks.

## Overview

This test bed provides:
- **Attack Simulation Scripts**: Automated tools to simulate various exfiltration attacks
- **Scenario Documentation**: Step-by-step guides for each attack type
- **Automated Testing**: Test runners to validate detection and prevention
- **Setup Tools**: Scripts to configure the test environment

## Quick Start

1. **Setup Test Environment**:
   ```bash
   cd scripts/test_bed
   ./setup_test_environment.sh
   ```

2. **Run a Specific Attack Scenario**:
   ```bash
   python attack_scripts/clipboard_exfil.py --vnc-host localhost --vnc-port 5900
   ```

3. **Run All Scenarios**:
   ```bash
   ./run_all_scenarios.sh
   ```

4. **Validate Detection**:
   ```bash
   python validation/check_incidents.py
   ```

## Directory Structure

```
test_bed/
├── README.md                    # This file
├── setup_test_environment.sh     # Environment setup script
├── run_all_scenarios.sh          # Run all attack scenarios
├── attack_scripts/               # Attack simulation scripts
│   ├── clipboard_exfil.py
│   ├── file_transfer_exfil.py
│   ├── dns_tunnel_exfil.py
│   ├── icmp_tunnel_exfil.py
│   ├── screenshot_burst.py
│   └── steganography_exfil.py
├── scenarios/                    # Scenario documentation
│   ├── SCENARIO_01_CLIPBOARD.md
│   ├── SCENARIO_02_FILE_TRANSFER.md
│   ├── SCENARIO_03_DNS_TUNNEL.md
│   ├── SCENARIO_04_ICMP_TUNNEL.md
│   ├── SCENARIO_05_SCREENSHOT_BURST.md
│   └── SCENARIO_06_STEGANOGRAPHY.md
├── validation/                   # Validation scripts
│   ├── check_incidents.py
│   └── verify_detection.py
└── utils/                        # Utility functions
    ├── vnc_client.py
    └── attack_helpers.py
```

## Prerequisites

- Python 3.8+
- TigerVNC or RealVNC server installed
- SentinelVNC proxy running
- Network access to VNC server

## Attack Scenarios

1. **Clipboard Exfiltration** - Copying sensitive data via clipboard
2. **File Transfer** - Transferring files through VNC
3. **DNS Tunneling** - Covert channel via DNS queries
4. **ICMP Tunneling** - Covert channel via ICMP packets
5. **Screenshot Burst** - Rapid screenshot capture
6. **Steganography** - Hidden data in images

See individual scenario files in `scenarios/` for detailed documentation.

