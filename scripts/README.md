# Scripts

Automation, tooling, and dev scripts for building, testing, and running the system.

## Test Bed

The test bed system (`test_bed/`) provides comprehensive attack simulation and validation tools for demonstrating VNC data exfiltration scenarios.

### Quick Start

1. **Setup environment**:
   ```bash
   cd scripts/test_bed
   ./setup_test_environment.sh
   ```

2. **Run all attack scenarios**:
   ```bash
   ./run_all_scenarios.sh
   ```

3. **Run specific scenario**:
   ```bash
   python attack_scripts/clipboard_exfil.py --vnc-host localhost --vnc-port 5900
   ```

4. **Validate detection**:
   ```bash
   python validation/check_incidents.py
   ```

See `test_bed/README.md` for detailed documentation.