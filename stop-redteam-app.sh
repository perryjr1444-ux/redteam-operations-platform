#!/usr/bin/env bash
#
# Stop Red Team Webapp cleanly
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CONTAINER_NAME="redteam-app"

echo -e "${BLUE}=== Stopping Red Team Webapp ===${NC}\n"

if podman ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}Stopping container '${CONTAINER_NAME}'...${NC}"
    podman stop ${CONTAINER_NAME}
    echo -e "${GREEN}✓ Container stopped${NC}"
else
    echo -e "${YELLOW}Container '${CONTAINER_NAME}' is not running${NC}"
fi

echo -e "\n${GREEN}Done!${NC}"
