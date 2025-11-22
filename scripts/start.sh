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
log "Starting infrastructure services (PostgreSQL, Redis, Zookeeper, Kafka, Ollama, Spark)..."
docker-compose up -d postgres redis zookeeper kafka ollama spark-master spark-worker-1 spark-worker-2

# Wait for infrastructure to be ready
log "Waiting for infrastructure services to be ready..."

# Wait for PostgreSQL
log "Waiting for PostgreSQL..."
for i in {1..30}; do
    if docker exec crypto-viz-postgres pg_isready -U crypto_viz -d crypto_analytics &>/dev/null; then
        success "PostgreSQL is ready!"
        break
    fi

    if [ $i -eq 30 ]; then
        warning "PostgreSQL took longer than expected, continuing anyway..."
        break
    fi

    echo -n "."
    sleep 2
done

# Wait for Redis
log "Waiting for Redis..."
for i in {1..15}; do
    if docker exec crypto-viz-redis redis-cli ping &>/dev/null; then
        success "Redis is ready!"
        break
    fi

    if [ $i -eq 15 ]; then
        warning "Redis took longer than expected, continuing anyway..."
        break
    fi

    echo -n "."
    sleep 2
done

# Wait for Zookeeper first (Kafka depends on it)
log "Waiting for Zookeeper..."
for i in {1..60}; do
    if echo stat | docker exec -i crypto-viz-zookeeper nc localhost 2181 | grep -q "Mode" 2>/dev/null; then
        success "Zookeeper is ready!"
        break
    fi

    if [ $i -eq 60 ]; then
        warning "Zookeeper took longer than expected, continuing anyway..."
        break
    fi

    echo -n "."
    sleep 3
done

# Wait for Kafka (needs more time after Zookeeper)
log "Waiting for Kafka..."
for i in {1..60}; do
    if docker logs crypto-viz-kafka 2>&1 | grep -q "started (kafka.server.KafkaServer)" 2>/dev/null; then
        success "Kafka is ready!"
        break
    fi

    if [ $i -eq 60 ]; then
        warning "Kafka took longer than expected, continuing anyway..."
        break
    fi

    echo -n "."
    sleep 5
done

# Wait for Ollama (optional service - don't fail if timeout)
log "Waiting for Ollama..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags &>/dev/null; then
        success "Ollama is ready!"
        break
    fi

    if [ $i -eq 30 ]; then
        warning "Ollama took longer than expected, continuing anyway..."
        warning "Sentiment analysis may not work until Ollama is ready"
        break
    fi

    echo -n "."
    sleep 10
done

# Initialize Ollama model if Ollama is running
if curl -s http://localhost:11434/api/tags &>/dev/null; then
    log "Initializing Ollama model (this may take a while)..."
    docker exec crypto-viz-ollama ollama pull gemma:2b 2>/dev/null || true
fi

# Wait for Spark
log "Waiting for Spark Master..."
for i in {1..30}; do
    if curl -s http://localhost:8082 &>/dev/null; then
        success "Spark Master is ready!"
        break
    fi

    if [ $i -eq 30 ]; then
        warning "Spark Master took longer than expected, continuing anyway..."
        warning "ML pipeline may not work until Spark is ready"
        break
    fi

    echo -n "."
    sleep 5
done

# Start application services
log "Starting application services..."
docker-compose up -d web-scraper analytics-builder backend

# Wait for backend
log "Waiting for backend API..."
for i in {1..40}; do
    if curl -s http://localhost:8000/health &>/dev/null; then
        success "Backend API is ready!"
        break
    fi

    if [ $i -eq 40 ]; then
        warning "Backend API took longer than expected"
        warning "Check logs with: docker logs crypto-viz-backend"
        break
    fi

    echo -n "."
    sleep 5
done

# Start frontend
log "Starting frontend..."
docker-compose up -d frontend

# Wait for frontend
log "Waiting for frontend..."
for i in {1..30}; do
    if curl -s http://localhost:3000 &>/dev/null; then
        success "Frontend is ready!"
        break
    fi

    if [ $i -eq 30 ]; then
        warning "Frontend took longer than expected"
        warning "Check logs with: docker logs crypto-viz-frontend"
        break
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