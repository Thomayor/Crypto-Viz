#!/bin/bash

# =====================================
# CRYPTO VIZ - Health Check Script
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
    echo -e "${GREEN}✅${NC} $1"
}

error() {
    echo -e "${RED}❌${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

echo -e "${BLUE}"
echo "=================================================="
echo "    CRYPTO VIZ - System Health Check"
echo "=================================================="
echo -e "${NC}"

# Global health status
OVERALL_HEALTH=true

# Check Docker status
log "Checking Docker environment..."
if ! docker info &> /dev/null; then
    error "Docker daemon is not running"
    OVERALL_HEALTH=false
else
    success "Docker daemon is running"
fi

# Check container status
log "Checking container status..."
echo ""

declare -A EXPECTED_CONTAINERS=(
    ["crypto-viz-zookeeper"]="Zookeeper"
    ["crypto-viz-kafka"]="Kafka"
    ["crypto-viz-ollama"]="Ollama AI"
    ["crypto-viz-spark-master"]="Spark Master"
    ["crypto-viz-spark-worker-1"]="Spark Worker 1"
    ["crypto-viz-spark-worker-2"]="Spark Worker 2"
    ["crypto-viz-web-scraper"]="Web Scraper"
    ["crypto-viz-analytics-builder"]="Analytics Builder"
    ["crypto-viz-backend"]="Backend API"
    ["crypto-viz-frontend"]="Frontend"
    ["crypto-viz-kafka-ui"]="Kafka UI"
)

for container in "${!EXPECTED_CONTAINERS[@]}"; do
    if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
        success "${EXPECTED_CONTAINERS[$container]} ($container)"
    else
        if docker ps -a --filter "name=$container" | grep -q "$container"; then
            error "${EXPECTED_CONTAINERS[$container]} ($container) - Container exists but not running"
        else
            error "${EXPECTED_CONTAINERS[$container]} ($container) - Container not found"
        fi
        OVERALL_HEALTH=false
    fi
done

echo ""
log "Checking service endpoints..."
echo ""

# Service health checks
declare -A SERVICES=(
    ["http://localhost:8000/health"]="Backend API"
    ["http://localhost:3000/health"]="Frontend"
    ["http://localhost:8081"]="Kafka UI"
    ["http://localhost:8080"]="Spark Master UI"
    ["http://localhost:11434/api/tags"]="Ollama API"
)

for endpoint in "${!SERVICES[@]}"; do
    if curl -s --max-time 10 "$endpoint" > /dev/null 2>&1; then
        success "${SERVICES[$endpoint]} ($endpoint)"
    else
        error "${SERVICES[$endpoint]} ($endpoint) - Not responding"
        OVERALL_HEALTH=false
    fi
done

echo ""
log "Checking Kafka topics..."

# Check Kafka topics
EXPECTED_TOPICS=("crypto-news" "crypto-prices" "social-posts" "analytics-data" "alerts")
if docker exec crypto-viz-kafka kafka-topics --bootstrap-server localhost:9092 --list &> /dev/null; then
    EXISTING_TOPICS=$(docker exec crypto-viz-kafka kafka-topics --bootstrap-server localhost:9092 --list 2>/dev/null)
    
    for topic in "${EXPECTED_TOPICS[@]}"; do
        if echo "$EXISTING_TOPICS" | grep -q "^$topic$"; then
            success "Kafka topic: $topic"
        else
            warning "Kafka topic missing: $topic"
        fi
    done
else
    error "Cannot connect to Kafka to check topics"
    OVERALL_HEALTH=false
fi

echo ""
log "Checking Ollama models..."

# Check Ollama models
if curl -s http://localhost:11434/api/tags | grep -q "llama3.1:8b"; then
    success "Ollama model: llama3.1:8b"
else
    warning "Ollama model missing: llama3.1:8b"
    echo "  Run: docker-compose up ollama-init"
fi

echo ""
log "Checking Spark cluster..."

# Check Spark workers
if curl -s http://localhost:8080 | grep -q "Workers (2)"; then
    success "Spark cluster: 2 workers connected"
elif curl -s http://localhost:8080 | grep -q "Workers (1)"; then
    warning "Spark cluster: Only 1 worker connected"
else
    error "Spark cluster: No workers connected"
    OVERALL_HEALTH=false
fi

echo ""
log "Checking data persistence..."

# Check volumes
EXPECTED_VOLUMES=("crypto-viz_shared_data" "crypto-viz_duckdb_data" "crypto-viz_kafka_data" "crypto-viz_ollama_data")
for volume in "${EXPECTED_VOLUMES[@]}"; do
    if docker volume ls | grep -q "$volume"; then
        success "Volume: $volume"
    else
        warning "Volume missing: $volume"
    fi
done

# Check DuckDB database
if docker exec crypto-viz-analytics-builder test -f /app/data/crypto_analytics.db 2>/dev/null; then
    success "DuckDB database file exists"
    
    # Check database tables
    TABLES=$(docker exec crypto-viz-analytics-builder python -c "
import duckdb
try:
    conn = duckdb.connect('/app/data/crypto_analytics.db')
    tables = conn.execute('SHOW TABLES').fetchall()
    print(','.join([table[0] for table in tables]))
    conn.close()
except Exception as e:
    print('ERROR')
" 2>/dev/null)
    
    if [ "$TABLES" != "ERROR" ] && [ ! -z "$TABLES" ]; then
        success "DuckDB tables: $TABLES"
    else
        warning "DuckDB database exists but no tables found"
    fi
else
    warning "DuckDB database file not found"
fi

echo ""
log "Resource usage check..."

# Check Docker resource usage
echo "Docker resource usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -n 10

echo ""
log "Disk usage check..."

# Check disk usage
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    error "Disk usage is at ${DISK_USAGE}% - Running low on space"
    OVERALL_HEALTH=false
elif [ "$DISK_USAGE" -gt 80 ]; then
    warning "Disk usage is at ${DISK_USAGE}% - Consider cleaning up"
else
    success "Disk usage is at ${DISK_USAGE}% - Sufficient space available"
fi

# Final health summary
echo ""
echo "=================================================="
if [ "$OVERALL_HEALTH" = true ]; then
    echo -e "${GREEN}🎉 OVERALL SYSTEM HEALTH: EXCELLENT${NC}"
    echo ""
    echo "All critical services are running properly!"
    echo "System is ready for crypto analysis."
    echo ""
    echo "📊 Access points:"
    echo "  • Dashboard: http://localhost:3000"
    echo "  • API: http://localhost:8000"
    echo "  • Monitoring: http://localhost:8081"
else
    echo -e "${RED}⚠️ OVERALL SYSTEM HEALTH: DEGRADED${NC}"
    echo ""
    echo "Some services are not functioning properly."
    echo "Check the errors above and run:"
    echo "  • docker-compose logs [service-name]"
    echo "  • scripts/restart.sh"
    echo ""
fi
echo "=================================================="