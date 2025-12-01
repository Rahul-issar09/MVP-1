#!/bin/bash

# SentinelVNC MVP - Complete Startup Script
# Run this script to start all services and the dashboard

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 Starting SentinelVNC MVP..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print section headers
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠️  Node.js not found. Installing dependencies for dashboard...${NC}"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Install dashboard dependencies
print_header "📦 Installing Dashboard Dependencies"
cd "$PROJECT_ROOT/dashboard"
if [ ! -d "node_modules" ]; then
    npm install
    echo -e "${GREEN}✓ Dashboard dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dashboard dependencies already installed${NC}"
fi

# Create blockchain data directory
print_header "📁 Setting Up Blockchain Gateway"
mkdir -p "$PROJECT_ROOT/blockchain_data"
echo -e "${GREEN}✓ Blockchain data directory ready${NC}"

# Print startup instructions
print_header "🎯 MVP Ready to Start"
echo ""
echo -e "${GREEN}Run these commands in separate terminals:${NC}"
echo ""
echo -e "${YELLOW}Terminal 1 - Blockchain Gateway:${NC}"
echo "  cd '$PROJECT_ROOT'"
echo "  python -m uvicorn blockchain.gateway:app --host 0.0.0.0 --port 8080"
echo ""
echo -e "${YELLOW}Terminal 2 - Forensics Service:${NC}"
echo "  cd '$PROJECT_ROOT/forensics'"
echo "  uvicorn main:app --host 0.0.0.0 --port 9000"
echo ""
echo -e "${YELLOW}Terminal 3 - Dashboard:${NC}"
echo "  cd '$PROJECT_ROOT/dashboard'"
echo "  npm run dev"
echo ""
echo -e "${GREEN}Dashboard will open at: http://localhost:3000${NC}"
echo ""
echo -e "${BLUE}Environment Variables (optional):${NC}"
echo "  export FABRIC_API_KEY=supersecret"
echo "  export REACT_APP_API_URL=http://localhost:9000"
echo ""
echo -e "${GREEN}✓ All systems ready for MVP demo!${NC}"
echo ""
