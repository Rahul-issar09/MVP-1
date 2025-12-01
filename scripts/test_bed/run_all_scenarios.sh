#!/bin/bash
# Run all attack scenarios in sequence

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VNC_HOST="${VNC_HOST:-localhost}"
VNC_PORT="${VNC_PORT:-5900}"
WAIT_BETWEEN="${WAIT_BETWEEN:-5}"  # seconds between scenarios

echo "=========================================="
echo "SentinelVNC Test Bed - Run All Scenarios"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  VNC Host: $VNC_HOST"
echo "  VNC Port: $VNC_PORT"
echo "  Wait between scenarios: ${WAIT_BETWEEN}s"
echo ""

# Check if VNC is accessible
echo "Checking VNC server connection..."
if nc -z "$VNC_HOST" "$VNC_PORT" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} VNC server is accessible"
else
    echo -e "${RED}✗${NC} Cannot connect to VNC server at $VNC_HOST:$VNC_PORT"
    echo "   Please ensure VNC server is running and accessible"
    exit 1
fi

# Check if Risk Engine is running
echo "Checking Risk Engine..."
if nc -z localhost 9000 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Risk Engine is running"
else
    echo -e "${RED}✗${NC} Risk Engine is not running on port 9000"
    echo "   Please start the Risk Engine before running scenarios"
    exit 1
fi

echo ""
echo "Starting attack scenarios..."
echo ""

# Scenarios to run
SCENARIOS=(
    "clipboard_exfil.py:Clipboard Exfiltration"
    "file_transfer_exfil.py:File Transfer Exfiltration"
    "dns_tunnel_exfil.py:DNS Tunneling"
    "icmp_tunnel_exfil.py:ICMP Tunneling"
    "screenshot_burst.py:Screenshot Burst"
    "steganography_exfil.py:Steganography"
)

SUCCESS_COUNT=0
FAIL_COUNT=0

for scenario_info in "${SCENARIOS[@]}"; do
    script=$(echo $scenario_info | cut -d: -f1)
    name=$(echo $scenario_info | cut -d: -f2)
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Scenario: $name${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if python3 "$SCRIPT_DIR/attack_scripts/$script" \
        --vnc-host "$VNC_HOST" \
        --vnc-port "$VNC_PORT"; then
        echo -e "${GREEN}✓${NC} Scenario completed successfully"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo -e "${RED}✗${NC} Scenario failed"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
    
    echo ""
    
    # Wait between scenarios (except for the last one)
    if [ "$scenario_info" != "${SCENARIOS[-1]}" ]; then
        echo "Waiting ${WAIT_BETWEEN} seconds before next scenario..."
        sleep "$WAIT_BETWEEN"
        echo ""
    fi
done

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "Summary"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Successful:${NC} $SUCCESS_COUNT"
echo -e "${RED}Failed:${NC} $FAIL_COUNT"
echo ""

# Check incidents
echo "Checking for detected incidents..."
if python3 "$SCRIPT_DIR/validation/check_incidents.py" --wait 2; then
    echo -e "${GREEN}✓${NC} Incidents detected"
else
    echo -e "${YELLOW}⚠${NC} No incidents found (this may be normal if detection thresholds are high)"
fi

echo ""
echo "Test bed run complete!"
echo ""
echo "To view detailed incident information:"
echo "  python3 $SCRIPT_DIR/validation/check_incidents.py"
echo ""
echo "To verify detection system:"
echo "  python3 $SCRIPT_DIR/validation/verify_detection.py"
echo ""

exit 0

