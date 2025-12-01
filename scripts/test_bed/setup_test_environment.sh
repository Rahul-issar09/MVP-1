#!/bin/bash
# Setup script for SentinelVNC test bed environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=========================================="
echo "SentinelVNC Test Bed Environment Setup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} Python found: $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check required Python packages
echo ""
echo "Checking Python dependencies..."
cd "$SCRIPT_DIR"

REQUIRED_PACKAGES=("httpx")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $package installed"
    else
        echo -e "${YELLOW}⚠${NC} $package not found"
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo ""
    echo "Installing missing packages..."
    pip3 install "${MISSING_PACKAGES[@]}" || {
        echo -e "${RED}✗${NC} Failed to install packages"
        exit 1
    }
fi

# Make scripts executable
echo ""
echo "Setting up script permissions..."
chmod +x "$SCRIPT_DIR/attack_scripts"/*.py 2>/dev/null || true
chmod +x "$SCRIPT_DIR/validation"/*.py 2>/dev/null || true
chmod +x "$SCRIPT_DIR/run_all_scenarios.sh" 2>/dev/null || true

echo -e "${GREEN}✓${NC} Scripts made executable"

# Create test data directory
echo ""
echo "Creating test data directories..."
mkdir -p "$PROJECT_ROOT/test_bed_data"
echo -e "${GREEN}✓${NC} Test data directory created"

# Check VNC server
echo ""
echo "Checking VNC server availability..."
if command -v vncserver &> /dev/null || command -v Xvnc &> /dev/null; then
    echo -e "${GREEN}✓${NC} VNC server found"
else
    echo -e "${YELLOW}⚠${NC} VNC server not found in PATH"
    echo "   You may need to install TigerVNC or RealVNC"
    echo "   For Ubuntu/Debian: sudo apt-get install tigervnc-standalone-server"
    echo "   For macOS: brew install tigervnc"
fi

# Check SentinelVNC services
echo ""
echo "Checking SentinelVNC services..."
echo "  (Make sure these are running before testing)"

SERVICES=(
    "Risk Engine:9000"
    "Response Engine:9200"
    "Forensics Service:9100"
    "Blockchain Gateway:8080"
)

for service in "${SERVICES[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if nc -z localhost $port 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $name is running on port $port"
    else
        echo -e "${YELLOW}⚠${NC} $name is not running on port $port"
    fi
done

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start SentinelVNC services (if not already running)"
echo "2. Start VNC server (TigerVNC or RealVNC)"
echo "3. Start SentinelVNC proxy"
echo "4. Run attack scenarios: ./run_all_scenarios.sh"
echo ""
echo "For detailed scenario documentation, see: scenarios/SCENARIO_*.md"

