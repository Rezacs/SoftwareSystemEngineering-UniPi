#!/bin/bash
# Reset runtime state and optionally stop services

RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}=========================================${NC}"
echo -e "${YELLOW}Segregation System - Reset${NC}"
echo -e "${YELLOW}=========================================${NC}"
echo ""

# Stop services
if [ -f stop_launcher.sh ]; then
    echo -e "${BLUE}→${NC} Stopping background services..."
    ./stop_launcher.sh
    echo ""
fi

# Reset runtime state
echo -e "${BLUE}→${NC} Resetting runtime state..."
python3 -m src.utils.reset_runtime_state

echo ""
echo -e "${YELLOW}Reset complete!${NC}"
echo ""
echo "To start again:"
echo "  1. Run: ./launcher.sh"
echo "  2. Run: python3 main.py"
echo ""
