#!/bin/bash
# Quick demo script for the Segregation System workflow

echo "=========================================="
echo "Segregation System - Quick Demo"
echo "=========================================="
echo ""
echo "This demo shows both modes of operation."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}1. Reset runtime state${NC}"
python3 -m src.utils.reset_runtime_state
echo ""

echo -e "${BLUE}2. Testing Mode Demo${NC}"
echo "This will show automatic decision simulation with 70/30 ratio"
echo ""
echo "To run the system in Testing mode:"
echo "  1. Launch: python3 main.py"
echo "  2. Select: [2] Testing"
echo "  3. The system will run continuously with simulated decisions"
echo ""

echo -e "${BLUE}3. Stop & Go Mode Demo${NC}"
echo "This will show interactive manual decision workflow"
echo ""
echo "To run the system in Stop & Go mode:"
echo "  1. Launch: python3 main.py"
echo "  2. Select: [1] Stop & Go"
echo "  3. Review reports when prompted"
echo "  4. Use helper scripts or edit JSON files:"
echo "     - python3 manual_set_balancing_decision.py true"
echo "     - python3 manual_set_coverage_decision.py true"
echo "  5. Relaunch: python3 main.py (after each decision)"
echo ""

echo -e "${GREEN}=========================================="
echo "Ready to start!"
echo "==========================================${NC}"
echo ""
echo "Remember to have the mock systems running:"
echo "  Terminal 1: python3 mock_upstream_system.py"
echo "  Terminal 2: python3 api.py"
echo "  Terminal 3: python3 mock_downstream_system.py"
echo ""
echo "Then send sessions with:"
echo "  curl -X POST http://127.0.0.1:5001/prepared-sessions/send \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"delay_seconds\": 1.0}'"
