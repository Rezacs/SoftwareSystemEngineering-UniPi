#!/bin/bash
# Launcher script for Segregation System
# This script starts all required mock systems and sends prepared sessions
# Then you can manually run: python3 main.py

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Segregation System - Launcher${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if a service is running
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

# Function to start a service in background
start_service() {
    local script=$1
    local name=$2
    local port=$3
    
    echo -e "${BLUE}→${NC} Starting $name..."
    nohup python3 "$script" > /dev/null 2>&1 &
    local pid=$!
    echo "$pid" >> .launcher_pids
    
    # Wait for service to be ready
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

# Create PID file for tracking background processes
> .launcher_pids

echo -e "${BLUE}Step 1: Checking and starting mock systems${NC}"
echo ""

# Check/start Mock Upstream (Preparation System)
if ! check_service 5001 "Mock Upstream System"; then
    start_service "mock_upstream_system.py" "Mock Upstream System" 5001
fi
echo ""

# Check/start REST API
if ! check_service 5002 "Segregation REST API"; then
    start_service "api.py" "Segregation REST API" 5002
fi
echo ""

# Check/start Mock Downstream (Development System)
if ! check_service 5003 "Mock Downstream System"; then
    start_service "mock_downstream_system.py" "Mock Downstream System" 5003
fi
echo ""

echo -e "${BLUE}Step 2: Sending prepared sessions${NC}"
echo ""

# Wait a moment for everything to stabilize
sleep 2

# Send prepared sessions
echo -e "${BLUE}→${NC} Sending prepared sessions batch..."
response=$(curl -s -X POST http://127.0.0.1:5001/prepared-sessions/send \
    -H "Content-Type: application/json" \
    -d '{"delay_seconds": 1.0}')

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Prepared sessions sent successfully"
    echo "   Response: $response"
else
    echo -e "${RED}✗${NC} Failed to send prepared sessions"
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}System ready!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "All mock systems are running in background."
echo ""
echo -e "${YELLOW}Next step:${NC}"
echo -e "  Run: ${BLUE}python3 main.py${NC}"
echo ""
echo "To stop all background services:"
echo -e "  Run: ${BLUE}./stop_launcher.sh${NC}"
echo ""

# Create a stop script
cat > stop_launcher.sh << 'STOP_SCRIPT'
#!/bin/bash
# Stop all services started by launcher.sh

if [ ! -f .launcher_pids ]; then
    echo "No services to stop (no .launcher_pids file found)"
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

echo -e "${BLUE}Tip:${NC} Services are running in background. Check logs with:"
echo "  ps aux | grep python3"
echo ""
