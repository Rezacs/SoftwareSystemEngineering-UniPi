#!/bin/bash
# End-to-End Test with Real Development System
# This script tests the complete pipeline:
# - Segregation System (this system)
# - Development System (real system, not mock)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     END-TO-END TEST: Segregation → Development System     ║${NC}"
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Configuration
SEGREGATION_API_PORT=5002
UPSTREAM_MOCK_PORT=5001
DEVELOPMENT_SYSTEM_PORT=5003
DEVELOPMENT_SYSTEM_DIR="../5-development"

# Function to check if a service is running
check_service() {
    local port=$1
    local name=$2
    
    if curl -s http://127.0.0.1:${port}/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name is running on port $port"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $name is NOT running on port $port"
        return 1
    fi
}

# Function to start a service in background
start_service() {
    local script=$1
    local name=$2
    local port=$3
    local dir=${4:-.}
    
    echo -e "${BLUE}→${NC} Starting $name in $dir..."
    
    if [ "$dir" != "." ]; then
        cd "$dir"
    fi
    
    nohup python3 "$script" > /dev/null 2>&1 &
    local pid=$!
    
    if [ "$dir" != "." ]; then
        cd "$SCRIPT_DIR"
    fi
    
    echo "$pid" >> .e2e_pids
    
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

# Create PID file for tracking
> .e2e_pids

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 1: Setting up services${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# 1. Start Mock Upstream (Preparation System simulator)
if ! check_service $UPSTREAM_MOCK_PORT "Mock Upstream System"; then
    start_service "3-prepSys_simulation.py" "Mock Upstream System" $UPSTREAM_MOCK_PORT "."
fi
echo ""

# 2. Start Segregation REST API
if ! check_service $SEGREGATION_API_PORT "Segregation REST API"; then
    start_service "api.py" "Segregation REST API" $SEGREGATION_API_PORT "."
fi
echo ""

# 3. Start REAL Development System
if ! check_service $DEVELOPMENT_SYSTEM_PORT "Development System"; then
    echo -e "${CYAN}→ Starting REAL Development System...${NC}"
    
    # Check if Development System directory exists
    if [ ! -d "$DEVELOPMENT_SYSTEM_DIR" ]; then
        echo -e "${RED}✗${NC} Development System directory not found: $DEVELOPMENT_SYSTEM_DIR"
        exit 1
    fi
    
    # Start Development System in background with input simulation
    cd "$DEVELOPMENT_SYSTEM_DIR"
    
    # We need to provide mode selection input automatically
    # Use 'yes' to automatically answer prompts
    echo -e "${YELLOW}  Note: Starting Development System in Testing mode (automatic)${NC}"
    (echo "2" | python3 main.py > /dev/null 2>&1) &
    local dev_pid=$!
    cd "$SCRIPT_DIR"
    echo "$dev_pid" >> .e2e_pids
    
    # Wait for it to be ready
    local attempts=0
    local max_attempts=30
    while [ $attempts -lt $max_attempts ]; do
        if curl -s http://127.0.0.1:${DEVELOPMENT_SYSTEM_PORT}/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Development System started (PID: $dev_pid)"
            break
        fi
        sleep 1
        attempts=$((attempts + 1))
    done
    
    if [ $attempts -eq $max_attempts ]; then
        echo -e "${RED}✗${NC} Development System failed to start"
        echo -e "${YELLOW}  You may need to start it manually:${NC}"
        echo -e "${YELLOW}  cd $DEVELOPMENT_SYSTEM_DIR && python3 main.py${NC}"
    fi
fi
echo ""

sleep 2

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 2: Checking configuration${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Check segregation config points to development system
SEGREGATION_CONFIG=$(cat config/config.json)
DEV_ENDPOINT=$(echo "$SEGREGATION_CONFIG" | grep developmentSystemEndpoint | cut -d'"' -f4)
echo -e "Segregation System target: ${CYAN}$DEV_ENDPOINT${NC}"

if [[ "$DEV_ENDPOINT" != *"5003"* ]]; then
    echo -e "${YELLOW}⚠ Warning: Development endpoint doesn't point to port 5003${NC}"
fi
echo ""

# Check how many sessions are available and needed
SESSIONS_AVAILABLE=$(ls data/input/prepared_session*.json 2>/dev/null | wc -l)
SESSIONS_NEEDED=$(echo "$SEGREGATION_CONFIG" | grep sufficientSessionNumber | grep -o '[0-9]\+')

echo -e "Sessions available: ${GREEN}$SESSIONS_AVAILABLE${NC}"
echo -e "Sessions needed: ${CYAN}$SESSIONS_NEEDED${NC}"

if [ "$SESSIONS_AVAILABLE" -lt "$SESSIONS_NEEDED" ]; then
    echo -e "${RED}✗ Not enough sessions! Need at least $SESSIONS_NEEDED${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 3: Sending prepared sessions${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${CYAN}→ Sending $SESSIONS_AVAILABLE prepared sessions...${NC}"

# Send sessions via the mock upstream system
response=$(curl -s -X POST http://127.0.0.1:$UPSTREAM_MOCK_PORT/prepared-sessions/send \
    -H "Content-Type: application/json" \
    -d '{"delay_seconds": 0.5}')

sent_count=$(echo "$response" | grep -o '"sent_count":[0-9]\+' | grep -o '[0-9]\+')
all_ok=$(echo "$response" | grep -o '"all_succeeded":[a-z]\+' | grep -o '[a-z]\+')

if [ "$all_ok" = "true" ]; then
    echo -e "${GREEN}✓${NC} All $sent_count sessions sent successfully"
else
    echo -e "${RED}✗${NC} Some sessions failed to send"
    echo "$response"
fi
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Step 4: Testing complete pipeline${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${CYAN}Now you can test the Segregation System:${NC}"
echo ""
echo -e "  ${YELLOW}1. Run Segregation System in Testing mode:${NC}"
echo -e "     python3 main.py"
echo -e "     Select: [2] Testing"
echo ""
echo -e "  ${YELLOW}2. Or run in Stop & Go mode:${NC}"
echo -e "     python3 main.py"
echo -e "     Select: [1] Stop & Go"
echo ""
echo -e "${GREEN}All services are running and sessions are loaded!${NC}"
echo ""

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Service Status${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
./check_status.sh

echo ""
echo -e "${CYAN}To stop all services:${NC}"
echo -e "  ./stop_e2e.sh"
echo ""

# Create stop script
cat > stop_e2e.sh << 'STOP_SCRIPT'
#!/bin/bash
# Stop all E2E test services

if [ ! -f .e2e_pids ]; then
    echo "No E2E services to stop"
    exit 0
fi

echo "Stopping E2E test services..."
while read pid; do
    if kill -0 $pid 2>/dev/null; then
        echo "Stopping process $pid"
        kill $pid 2>/dev/null || true
    fi
done < .e2e_pids

rm -f .e2e_pids
echo "All E2E services stopped"
STOP_SCRIPT

chmod +x stop_e2e.sh
