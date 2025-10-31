#!/usr/bin/env bash
#
# Full cleanup of Red Team Webapp (containers, images, volumes)
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CONTAINER_NAME="redteam-app"
IMAGE_NAME="localhost/redteam_py_app_app"
NETWORK_NAME="redteam_py_app_redteam-network"

echo -e "${BLUE}=== Full Cleanup of Red Team Webapp ===${NC}\n"
echo -e "${YELLOW}This will remove:${NC}"
echo "  - Container: ${CONTAINER_NAME}"
echo "  - Image: ${IMAGE_NAME}"
echo "  - Network: ${NETWORK_NAME}"
echo "  - Build cache"
echo ""
echo -e "${RED}This will NOT remove:${NC}"
echo "  - Database files (./db/)"
echo "  - Log files (./logs/)"
echo ""

read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cancelled${NC}"
    exit 0
fi

echo ""

# Stop and remove container
if podman ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}Stopping and removing container...${NC}"
    podman stop ${CONTAINER_NAME} 2>/dev/null || true
    podman rm ${CONTAINER_NAME} 2>/dev/null || true
    echo -e "${GREEN}✓ Container removed${NC}"
else
    echo -e "${GREEN}✓ No container to remove${NC}"
fi

# Remove image
if podman images --format "{{.Repository}}:{{.Tag}}" | grep -q "${IMAGE_NAME}"; then
    echo -e "${YELLOW}Removing image...${NC}"
    podman rmi ${IMAGE_NAME} 2>/dev/null || true
    echo -e "${GREEN}✓ Image removed${NC}"
else
    echo -e "${GREEN}✓ No image to remove${NC}"
fi

# Remove network
if podman network ls --format "{{.Name}}" | grep -q "^${NETWORK_NAME}$"; then
    echo -e "${YELLOW}Removing network...${NC}"
    podman network rm ${NETWORK_NAME} 2>/dev/null || true
    echo -e "${GREEN}✓ Network removed${NC}"
else
    echo -e "${GREEN}✓ No network to remove${NC}"
fi

# Prune build cache
echo -e "${YELLOW}Pruning build cache...${NC}"
podman system prune -f > /dev/null 2>&1 || true
echo -e "${GREEN}✓ Build cache pruned${NC}"

echo -e "\n${GREEN}Cleanup complete!${NC}"
echo -e "\nTo rebuild and start: ${YELLOW}./start-redteam-app.sh${NC}"
