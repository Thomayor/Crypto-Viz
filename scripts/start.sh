#!/bin/bash

# =====================================
# CRYPTO VIZ - Startup Script
# =====================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo -e "${BLUE}"
echo "=================================================="
echo "    CRYPTO VIZ - Infrastructure Startup"
echo "=================================================="
echo -e "${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    warning ".env file not found!"
    if [ -f ".env.example" ]; then
        log "Creating .env from .env.example..."
        cp .env.example .env
        warning "Please configure your .env file with proper values before continuing!"
        exit 1
    else
        error ".env.example file not found! Cannot create .env file."
        exit 1
    fi
else
    success ".env file found"
fi

# Check for required commands
check_command() {
    if ! command -v $1 &> /dev/null; then
        error "$1 is required but not installed."
        exit 1
    fi
}

log "Checking required commands..."
check_command docker
check_command docker-compose
success "All required commands are available"

# Check Docker daemon
log "Checking Docker daemon..."
if ! docker info &> /dev/null; then
    error "Docker daemon is not running!"
    exit 1
fi
success "Docker daemon is running"

# Create necessary directories
log "Creating necessary directories..."
mkdir -p data/{analytics,parquet,scraping}
mkdir -p logs
mkdir -p services/{scraper,analytics}/config
mkdir -p backend/static
mkdir -p frontend/dist
success "Directories created"

# Check available disk space (minimum 5GB recommended)
log "Checking available disk space..."
AVAILABLE_SPACE=$(df . | awk 'NR==2 {print $4}')
REQUIRED_SPACE=5242880  # 5GB in KB

if [ $AVAILABLE_SPACE -lt $REQUIRED_SPACE ]; then
    warning "Available disk space is less than 5GB. This might cause issues."
    warning "Available: $(($AVAILABLE_SPACE / 1024 / 1024))GB, Recommended: 5GB"
fi

# Stop any existing containers
log "Stopping existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true

# Pull latest images
log "Pulling latest Docker images..."
docker-compose pull

# Build custom images
log "Building custom images..."
docker-compose build --parallel

# Start infrastructure services first
log "Starting infrastructure services (Kafka, Zookeeper, Ollama, Spark)..."
docker-compose up -d zookeeper kafka ollama spark-master spark-worker-1 spark-worker-2

# Wait for infrastructure to be ready
log "Waiting for infrastructure services to be ready..."

# Wait for Kafka
log "Waiting for Kafka..."
for i in {1..30}; do
    if docker-compose exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092 &>/dev/null; then
        success "Kafka is ready!"
        break
    fi
    
    if [ $i -eq 30 ]; then
        error "Kafka failed to start within timeout"
        exit 1
    fi
    
    echo -n "."
    sleep 10
done

# Wait for Ollama
log "Waiting for Ollama..."
for i in {1..20}; do
    if curl -s http://localhost:11434/api/tags &>/dev/null; then
        success "Ollama is ready!"
        break
    fi
    
    if [ $i -eq 20 ]; then
        error "Ollama failed to start within timeout"
        exit 1
    fi
    
    echo -n "."
    sleep 15
done

# Initialize Ollama model
log "Initializing Ollama model (this may take a while)..."
docker exec crypto-viz-ollama ollama pull llama3.1:8b 2>/dev/null || true

# Wait for Spark
log "Waiting for Spark Master..."
for i in {1..15}; do
    if curl -s http://localhost:8082 | grep -q "Spark Master" 2>/dev/null; then
        success "Spark Master is ready!"
        break
    fi
    
    if [ $i -eq 15 ]; then
        error "Spark Master failed to start within timeout"
        exit 1
    fi
    
    echo -n "."
    sleep 10
done

# Start application services
log "Starting application services..."
docker-compose up -d web-scraper analytics-builder backend

# Wait for backend
log "Waiting for backend API..."
for i in {1..20}; do
    if curl -s http://localhost:8000/health &>/dev/null; then
        success "Backend API is ready!"
        break
    fi
    
    if [ $i -eq 20 ]; then
        error "Backend API failed to start within timeout"
        exit 1
    fi
    
    echo -n "."
    sleep 10
done

# Start frontend
log "Starting frontend..."
docker-compose up -d frontend

# Wait for frontend
log "Waiting for frontend..."
for i in {1..15}; do
    if curl -s http://localhost:3000/health &>/dev/null; then
        success "Frontend is ready!"
        break
    fi
    
    if [ $i -eq 15 ]; then
        error "Frontend failed to start within timeout"
        exit 1
    fi
    
    echo -n "."
    sleep 5
done

# Start monitoring services
log "Starting monitoring services..."
docker-compose up -d kafka-ui

echo -e "${GREEN}"
echo "=================================================="
echo "    🚀 CRYPTO VIZ SUCCESSFULLY STARTED! 🚀"
echo "=================================================="
echo -e "${NC}"

echo "📊 Services are now available at:"
echo "  • Frontend:        http://localhost:3000"
echo "  • Backend API:     http://localhost:8000"
echo "  • Kafka UI:        http://localhost:8081"
echo "  • Spark Master UI: http://localhost:8080"
echo "  • Ollama:          http://localhost:11434"
echo ""
echo "🔍 Service Status:"
echo "  • Run 'docker-compose ps' to check all services"
echo "  • Run 'docker-compose logs [service-name]' to view logs"
echo "  • Run 'scripts/stop.sh' to stop all services"
echo ""
echo "📝 Next Steps:"
echo "  1. Configure your APIs in .env file if not done yet"
echo "  2. Check service logs: docker-compose logs -f"
echo "  3. Access the dashboard at http://localhost:3000"
echo ""
echo "🐛 Troubleshooting:"
echo "  • Check logs: docker-compose logs -f [service-name]"
echo "  • Restart service: docker-compose restart [service-name]"
echo "  • Full restart: scripts/restart.sh"
echo ""

# Final health check
log "Running final health check..."
sleep 10

SERVICES=("kafka:29092" "ollama:11434" "backend:8000" "frontend:3000")
ALL_HEALTHY=true

for service in "${SERVICES[@]}"; do
    IFS=':' read -r host port <<< "$service"
    case $host in
        "kafka")
            if docker-compose exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092 &>/dev/null; then
                echo "  ✅ Kafka: Healthy"
            else
                echo "  ❌ Kafka: Unhealthy"
                ALL_HEALTHY=false
            fi
            ;;
        "ollama")
            if curl -s http://localhost:11434/api/tags &>/dev/null; then
                echo "  ✅ Ollama: Healthy"
            else
                echo "  ❌ Ollama: Unhealthy"
                ALL_HEALTHY=false
            fi
            ;;
        "backend")
            if curl -s http://localhost:8000/health &>/dev/null; then
                echo "  ✅ Backend: Healthy"
            else
                echo "  ❌ Backend: Unhealthy"
                ALL_HEALTHY=false
            fi
            ;;
        "frontend")
            if curl -s http://localhost:3000/health &>/dev/null; then
                echo "  ✅ Frontend: Healthy"
            else
                echo "  ❌ Frontend: Unhealthy"
                ALL_HEALTHY=false
            fi
            ;;
    esac
done

echo ""
if [ "$ALL_HEALTHY" = true ]; then
    success "🎉 All services are healthy and ready to use!"
else
    warning "⚠️ Some services are not healthy. Check the logs for details."
    echo "Run 'docker-compose logs [service-name]' to investigate issues."
fi

echo ""
echo -e "${BLUE}Happy crypto analyzing! 🚀📈${NC}"