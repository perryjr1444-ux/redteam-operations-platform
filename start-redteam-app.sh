#!/usr/bin/env bash
#
# Smart startup script for Red Team Webapp
# Handles common roadblocks automatically
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="redteam-app"
IMAGE_NAME="localhost/redteam_py_app_app"
PORT=5172
PROJECT_DIR="/opt/projects/redteam_py_app"
FORCE_REBUILD=${FORCE_REBUILD:-false}

echo -e "${BLUE}=== Red Team Webapp Startup ===${NC}\n"

# Step 1: Check prerequisites
echo -e "${YELLOW}[1/7]${NC} Checking prerequisites..."

# Check if podman is installed
if ! command -v podman &> /dev/null; then
    echo -e "${RED}ERROR: podman is not installed${NC}"
    exit 1
fi

# Check if podman machine is running
if ! podman machine list | grep -q "Currently running"; then
    echo -e "${YELLOW}Starting podman machine...${NC}"
    podman machine start || {
        echo -e "${RED}ERROR: Failed to start podman machine${NC}"
        exit 1
    }
fi

# Check if podman-compose is available
if ! command -v podman-compose &> /dev/null; then
    echo -e "${RED}ERROR: podman-compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}\n"

# Step 2: Check and handle existing container
echo -e "${YELLOW}[2/7]${NC} Checking for existing containers..."

if podman ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}Found existing container '${CONTAINER_NAME}'. Removing...${NC}"

    # Stop if running
    if podman ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        podman stop ${CONTAINER_NAME} || true
    fi

    # Remove container
    podman rm ${CONTAINER_NAME} || true
    echo -e "${GREEN}✓ Old container removed${NC}"
else
    echo -e "${GREEN}✓ No existing container found${NC}"
fi
echo ""

# Step 3: Check port availability
echo -e "${YELLOW}[3/7]${NC} Checking port ${PORT}..."

if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}WARNING: Port ${PORT} is in use by another process${NC}"
    echo -e "You may need to stop the other process or change the port in docker-compose.yml"
    # Continue anyway - docker might handle it
fi
echo -e "${GREEN}✓ Port check complete${NC}\n"

# Step 4: Ensure required directories exist
echo -e "${YELLOW}[4/7]${NC} Setting up directories and quantum seed..."

cd "${PROJECT_DIR}"

mkdir -p db logs

# Initialize quantum seed if using quantum key generation
if [ ! -f "db/.quantum_seed" ]; then
    echo -e "${YELLOW}Initializing quantum key derivation system...${NC}"
    echo -e "${BLUE}   Crystal Lattice KDF will auto-generate master seed on first run${NC}"
else
    echo -e "${GREEN}✓ Quantum seed exists${NC}"
fi

echo -e "${GREEN}✓ Directories ready${NC}\n"

# Step 5: Build or rebuild image
echo -e "${YELLOW}[5/7]${NC} Building container image..."

if [ "$FORCE_REBUILD" = "true" ]; then
    echo -e "${YELLOW}Force rebuild requested. Removing old image...${NC}"
    podman rmi ${IMAGE_NAME} 2>/dev/null || true
fi

podman-compose build || {
    echo -e "${RED}ERROR: Build failed${NC}"
    exit 1
}

echo -e "${GREEN}✓ Image built successfully${NC}\n"

# Step 6: Start the container
echo -e "${YELLOW}[6/7]${NC} Starting container..."

podman-compose up -d || {
    echo -e "${RED}ERROR: Failed to start container${NC}"
    echo -e "${YELLOW}Showing logs:${NC}"
    podman logs ${CONTAINER_NAME} 2>&1 || true
    exit 1
}

echo -e "${GREEN}✓ Container started${NC}\n"

# Step 7: Wait for application to be ready
echo -e "${YELLOW}[7/7]${NC} Waiting for application to be ready..."

MAX_WAIT=60
WAIT_COUNT=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -s -f http://localhost:${PORT}/api/liveness > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Application is ready!${NC}\n"
        break
    fi

    echo -n "."
    sleep 2
    WAIT_COUNT=$((WAIT_COUNT + 2))

    # Check if container is still running
    if ! podman ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "\n${RED}ERROR: Container stopped unexpectedly${NC}"
        echo -e "${YELLOW}Showing logs:${NC}"
        podman logs ${CONTAINER_NAME}
        exit 1
    fi
done

if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
    echo -e "\n${YELLOW}WARNING: Application did not respond within ${MAX_WAIT}s${NC}"
    echo -e "${YELLOW}Showing logs:${NC}"
    podman logs ${CONTAINER_NAME}
    echo -e "\n${YELLOW}Container may still be starting up...${NC}"
fi

# Final status check
echo -e "${BLUE}=== Status ===${NC}"

# Check health endpoint
if curl -k -s https://localhost:${PORT}/api/health > /dev/null 2>&1; then
    HEALTH=$(curl -k -s https://localhost:${PORT}/api/health | python3 -m json.tool 2>/dev/null || echo "OK")
    echo -e "${GREEN}Health Check:${NC} Passed"
    echo "$HEALTH" | head -5
else
    echo -e "${YELLOW}Health Check:${NC} Not ready yet"
fi

echo -e "\n${BLUE}=== Access Information ===${NC}"
echo -e "Application URL:  ${GREEN}https://localhost:${PORT}${NC} 🔒"
echo -e "API Health:       ${GREEN}https://localhost:${PORT}/api/health${NC}"
echo -e "Dashboard:        ${GREEN}https://localhost:${PORT}/${NC}"

# Check if quantum seed was generated
if [ -f "db/.quantum_seed" ]; then
    echo -e "\n${BLUE}=== Security Information ===${NC}"
    echo -e "Key Generation:   ${GREEN}Quantum-Inspired Crystal Lattice KDF${NC}"
    echo -e "Master Seed:      ${GREEN}db/.quantum_seed${NC}"
    echo -e "Security Level:   ${GREEN}Maximum (384-bit derived key)${NC}"
fi

echo -e "\n${BLUE}=== Management Commands ===${NC}"
echo -e "View logs:        ${YELLOW}./logs-redteam-app.sh${NC}"
echo -e "Stop app:         ${YELLOW}./stop-redteam-app.sh${NC}"
echo -e "Restart app:      ${YELLOW}./restart-redteam-app.sh${NC}"
echo -e "Full cleanup:     ${YELLOW}./clean-redteam-app.sh${NC}"
echo -e "\n${GREEN}Startup complete!${NC}"
