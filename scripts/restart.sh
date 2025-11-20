#!/bin/bash

# =====================================
# CRYPTO VIZ - Restart Script
# =====================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

echo -e "${BLUE}"
echo "=================================================="
echo "    CRYPTO VIZ - Infrastructure Restart"
echo "=================================================="
echo -e "${NC}"

# Parse command line arguments
REBUILD=false
CLEAN_VOLUMES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --rebuild)
            REBUILD=true
            shift
            ;;
        --clean)
            CLEAN_VOLUMES=true
            shift
            ;;
        --full)
            REBUILD=true
            CLEAN_VOLUMES=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --rebuild       Rebuild Docker images before restart"
            echo "  --clean         Clean volumes (removes all data)"
            echo "  --full          Full restart (rebuild + clean)"
            echo "  -h, --help      Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0               # Simple restart"
            echo "  $0 --rebuild     # Restart with image rebuild"
            echo "  $0 --full        # Complete restart with cleanup"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Stop services
log "Stopping current services..."
if [ "$CLEAN_VOLUMES" = true ]; then
    ./scripts/stop.sh --volumes
else
    ./scripts/stop.sh
fi

# Rebuild if requested
if [ "$REBUILD" = true ]; then
    log "Rebuilding Docker images..."
    docker-compose build --no-cache --parallel
fi

# Clean Docker system
log "Cleaning Docker system..."
docker system prune -f

# Start services
log "Starting services..."
./scripts/start.sh

echo -e "${GREEN}"
echo "=================================================="
echo "    🔄 CRYPTO VIZ RESTART COMPLETE"
echo "=================================================="
echo -e "${NC}"