#!/usr/bin/env bash
#
# Quick restart Red Team Webapp (no rebuild)
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CONTAINER_NAME="redteam-app"
PORT=5172

echo -e "${BLUE}=== Restarting Red Team Webapp ===${NC}\n"

# Stop if running
if podman ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}Stopping container...${NC}"
    podman stop ${CONTAINER_NAME}
    echo -e "${GREEN}✓ Stopped${NC}"
fi

# Start container
echo -e "${YELLOW}Starting container...${NC}"
podman start ${CONTAINER_NAME} || {
    echo -e "${YELLOW}Container doesn't exist. Run ./start-redteam-app.sh instead${NC}"
    exit 1
}

echo -e "${GREEN}✓ Started${NC}\n"

# Wait for ready
echo -e "${YELLOW}Waiting for application...${NC}"
sleep 3

if curl -s -f http://localhost:${PORT}/api/liveness > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Application is ready!${NC}"
    echo -e "\nAccess at: ${GREEN}http://localhost:${PORT}${NC}"
else
    echo -e "${YELLOW}Application may still be starting up${NC}"
    echo -e "Run './logs-redteam-app.sh' to check status"
fi

echo -e "\n${GREEN}Done!${NC}"
