#!/bin/bash
# Enhanced Launcher with option to use real Development System
# Usage: ./launcher_with_dev.sh [--real-dev]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if --real-dev flag is provided
USE_REAL_DEV=false
if [ "$1" = "--real-dev" ]; then
    USE_REAL_DEV=true
    echo -e "${YELLOW}Mode: Using REAL Development System${NC}"
else
    echo -e "${YELLOW}Mode: Using Mock Development System${NC}"
    echo -e "${YELLOW}Tip: Use --real-dev to test with the real Development System${NC}"
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Segregation System - Enhanced Launcher${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Configuration
DEVELOPMENT_SYSTEM_DIR="../5-development"

check_service() {
    local port=$1
    local name=$2
    
    if curl -s http://127.0.0.1:${port}/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is already running on port $port"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $name is not running on port $port"
        return 1
    fi
}

start_service() {
    local script=$1
    local name=$2
    local port=$3
    
    echo -e "${BLUE}→${NC} Starting $name..."
    nohup python3 "$script" > /dev/null 2>&1 &
    local pid=$!
    echo "$pid" >> .launcher_pids
    
    local attempts=0
    local max_attempts=30
    while [ $attempts -lt $max_attempts ]; do
        if curl -s http://127.0.0.1:${port}/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} $name started successfully (PID: $pid)"
            return 0
        fi
        sleep 1
        attempts=$((attempts + 1))
    done
    
    echo -e "${RED}✗${NC} Failed to start $name"
    return 1
}

> .launcher_pids

echo -e "${BLUE}Step 1: Starting services${NC}"
echo ""

# Mock Upstream
if ! check_service 5001 "Mock Upstream System"; then
    start_service "3-prepSys_simulation.py" "Mock Upstream System" 5001
fi
echo ""

# REST API
if ! check_service 5002 "Segregation REST API"; then
    start_service "api.py" "Segregation REST API" 5002
fi
echo ""

# Downstream: Real Development or Mock
if $USE_REAL_DEV; then
    if ! check_service 5003 "Development System"; then
        echo -e "${BLUE}→${NC} Starting REAL Development System..."
        
        if [ ! -d "$DEVELOPMENT_SYSTEM_DIR" ]; then
            echo -e "${RED}✗${NC} Development System directory not found: $DEVELOPMENT_SYSTEM_DIR"
            exit 1
        fi
        
        cd "$DEVELOPMENT_SYSTEM_DIR"
        (echo "2" | python3 main.py > /dev/null 2>&1) &
        local dev_pid=$!
        cd "$SCRIPT_DIR"
        echo "$dev_pid" >> .launcher_pids
        
        local attempts=0
        while [ $attempts -lt 30 ]; do
            if curl -s http://127.0.0.1:5003/health > /dev/null 2>&1; then
                echo -e "${GREEN}✓${NC} Development System started (PID: $dev_pid)"
                break
            fi
            sleep 1
            attempts=$((attempts + 1))
        done
    fi
else
    if ! check_service 5003 "Mock Downstream System"; then
        start_service "5-devSys_simulation.py" "Mock Downstream System" 5003
    fi
fi
echo ""

echo -e "${BLUE}Step 2: Sending prepared sessions${NC}"
echo ""

sleep 2

echo -e "${BLUE}→${NC} Sending prepared sessions batch..."
response=$(curl -s -X POST http://127.0.0.1:5001/prepared-sessions/send \
    -H "Content-Type: application/json" \
    -d '{"delay_seconds": 0.5}')

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Prepared sessions sent successfully"
    sent_count=$(echo "$response" | grep -o '"sent_count":[0-9]\+' | grep -o '[0-9]\+' || echo "?")
    echo "   Sent: $sent_count sessions"
else
    echo -e "${RED}✗${NC} Failed to send prepared sessions"
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}System ready!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Services running:"
if $USE_REAL_DEV; then
    echo "  - Mock Upstream (port 5001)"
    echo "  - Segregation API (port 5002)"
    echo "  - REAL Development System (port 5003)"
else
    echo "  - Mock Upstream (port 5001)"
    echo "  - Segregation API (port 5002)"
    echo "  - Mock Development System (port 5003)"
fi
echo ""
echo -e "${YELLOW}Next step:${NC}"
echo -e "  Run: ${BLUE}python3 main.py${NC}"
echo ""
echo "To stop all services:"
echo -e "  Run: ${BLUE}./stop_launcher.sh${NC}"
echo ""

# Create stop script
cat > stop_launcher.sh << 'STOP_SCRIPT'
#!/bin/bash
if [ ! -f .launcher_pids ]; then
    echo "No services to stop"
    exit 0
fi

echo "Stopping services..."
while read pid; do
    if kill -0 $pid 2>/dev/null; then
        echo "Stopping process $pid"
        kill $pid 2>/dev/null || true
    fi
done < .launcher_pids

rm -f .launcher_pids
echo "All services stopped"
STOP_SCRIPT

chmod +x stop_launcher.sh
