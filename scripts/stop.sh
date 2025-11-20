#!/bin/bash

# =====================================
# CRYPTO VIZ - Stop Script
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

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo -e "${BLUE}"
echo "=================================================="
echo "    CRYPTO VIZ - Infrastructure Shutdown"
echo "=================================================="
echo -e "${NC}"

# Parse command line arguments
REMOVE_VOLUMES=false
REMOVE_IMAGES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --volumes)
            REMOVE_VOLUMES=true
            shift
            ;;
        --images)
            REMOVE_IMAGES=true
            shift
            ;;
        --all)
            REMOVE_VOLUMES=true
            REMOVE_IMAGES=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --volumes    Remove volumes (will delete all data)"
            echo "  --images     Remove built images"
            echo "  --all        Remove both volumes and images"
            echo "  -h, --help   Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Stop services only"
            echo "  $0 --volumes          # Stop services and remove volumes"
            echo "  $0 --all              # Complete cleanup"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Stop services gracefully
log "Stopping CRYPTO VIZ services..."

# Stop application services first
log "Stopping application services..."
docker-compose stop frontend backend analytics-builder web-scraper healthcheck-monitor kafka-ui 2>/dev/null || true

# Stop infrastructure services
log "Stopping infrastructure services..."
docker-compose stop spark-worker-2 spark-worker-1 spark-master ollama kafka zookeeper 2>/dev/null || true

# Remove containers
log "Removing containers..."
docker-compose down --remove-orphans

success "All services stopped successfully"

# Remove volumes if requested
if [ "$REMOVE_VOLUMES" = true ]; then
    warning "Removing volumes (this will delete all data)..."
    echo "This action cannot be undone. Continuing in 5 seconds..."
    echo "Press Ctrl+C to cancel..."
    sleep 5
    
    docker-compose down -v
    success "Volumes removed"
fi

# Remove images if requested
if [ "$REMOVE_IMAGES" = true ]; then
    log "Removing built images..."
    
    # Remove crypto-viz images
    docker images --format "table {{.Repository}}:{{.Tag}}" | grep crypto-viz | while read image; do
        if [ ! -z "$image" ] && [ "$image" != "REPOSITORY:TAG" ]; then
            log "Removing image: $image"
            docker rmi "$image" 2>/dev/null || true
        fi
    done
    
    # Remove dangling images
    docker image prune -f
    success "Images removed"
fi

# Show final status
echo ""
echo -e "${GREEN}"
echo "=================================================="
echo "    ✅ CRYPTO VIZ SHUTDOWN COMPLETE"
echo "=================================================="
echo -e "${NC}"

if [ "$REMOVE_VOLUMES" = true ]; then
    echo "⚠️  All data has been removed (volumes deleted)"
fi

if [ "$REMOVE_IMAGES" = true ]; then
    echo "🗑️  Built images have been removed"
fi

echo ""
echo "To start the system again:"
echo "  scripts/start.sh"
echo ""
echo "To view remaining Docker resources:"
echo "  docker ps -a"
echo "  docker images"
echo "  docker volume ls"