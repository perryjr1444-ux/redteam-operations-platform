#!/usr/bin/env bash
#
# View Red Team Webapp logs
#

# Colors
BLUE='\033[0;34m'
NC='\033[0m'

CONTAINER_NAME="redteam-app"

echo -e "${BLUE}=== Red Team Webapp Logs ===${NC}"
echo -e "${BLUE}Press Ctrl+C to exit${NC}\n"

# Follow logs if container is running, otherwise show last logs
if podman ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    podman logs -f ${CONTAINER_NAME}
else
    echo "Container is not running. Showing last logs:"
    podman logs ${CONTAINER_NAME} 2>/dev/null || echo "No logs available"
fi
