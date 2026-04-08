#!/bin/bash
# Check status of all services

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================="
echo "Service Status Check"
echo "========================================="
echo ""

check_port() {
    local port=$1
    local name=$2
    
    if curl -s http://127.0.0.1:${port}/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is running on port $port"
    else
        echo -e "${RED}✗${NC} $name is NOT running on port $port"
    fi
}

check_port 5001 "Mock Upstream System   "
check_port 5002 "Segregation REST API   "
check_port 5003 "Mock Downstream System "

echo ""
echo "Background processes started by launcher:"
if [ -f .launcher_pids ]; then
    while read pid; do
        if kill -0 $pid 2>/dev/null; then
            echo -e "  ${GREEN}→${NC} Process $pid is running"
        else
            echo -e "  ${YELLOW}→${NC} Process $pid is not running"
        fi
    done < .launcher_pids
else
    echo "  No launcher PIDs file found"
fi

echo ""
