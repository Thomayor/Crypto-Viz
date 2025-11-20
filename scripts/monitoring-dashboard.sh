#!/bin/bash

# =====================================
# CRYPTO VIZ - Monitoring Dashboard
# =====================================
# Real-time monitoring dashboard for all services

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Clear screen and show header
clear_and_header() {
    clear
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║          CRYPTO VIZ - MONITORING DASHBOARD                    ║"
    echo "║          $(date +'%Y-%m-%d %H:%M:%S')                              ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check service health
check_service() {
    local container=$1
    local name=$2

    if docker ps --filter "name=$container" --filter "status=running" --format "{{.Names}}" | grep -q "$container"; then
        echo -e "${GREEN}●${NC} $name"
        return 0
    else
        echo -e "${RED}●${NC} $name"
        return 1
    fi
}

# Get container stats
get_container_stats() {
    local container=$1
    docker stats --no-stream --format "{{.CPUPerc}}\t{{.MemUsage}}" "$container" 2>/dev/null || echo "N/A\tN/A"
}

# Get Kafka metrics
get_kafka_metrics() {
    local topics=$(docker exec crypto-viz-kafka kafka-topics --bootstrap-server localhost:9092 --list 2>/dev/null | wc -l)
    echo "$topics"
}

# Main monitoring loop
monitor_loop() {
    while true; do
        clear_and_header

        echo -e "${BLUE}=== CORE SERVICES ===${NC}"
        check_service "crypto-viz-zookeeper" "Zookeeper"
        check_service "crypto-viz-kafka" "Kafka Broker"
        check_service "crypto-viz-kafka-ui" "Kafka UI"
        echo ""

        echo -e "${BLUE}=== PROCESSING SERVICES ===${NC}"
        check_service "crypto-viz-spark-master" "Spark Master"
        check_service "crypto-viz-spark-worker-1" "Spark Worker 1"
        check_service "crypto-viz-spark-worker-2" "Spark Worker 2"
        check_service "crypto-viz-ollama" "Ollama AI"
        echo ""

        echo -e "${BLUE}=== APPLICATION SERVICES ===${NC}"
        check_service "crypto-viz-web-scraper" "Web Scraper"
        check_service "crypto-viz-analytics-builder" "Analytics Builder"
        check_service "crypto-viz-backend" "Backend API"
        check_service "crypto-viz-frontend" "Frontend"
        echo ""

        echo -e "${BLUE}=== MONITORING SERVICES ===${NC}"
        check_service "crypto-viz-prometheus" "Prometheus" 2>/dev/null || echo -e "${YELLOW}○${NC} Prometheus (not started)"
        check_service "crypto-viz-grafana" "Grafana" 2>/dev/null || echo -e "${YELLOW}○${NC} Grafana (not started)"
        check_service "crypto-viz-loki" "Loki" 2>/dev/null || echo -e "${YELLOW}○${NC} Loki (not started)"
        echo ""

        echo -e "${BLUE}=== KAFKA METRICS ===${NC}"
        KAFKA_TOPICS=$(get_kafka_metrics)
        echo -e "Topics: ${GREEN}${KAFKA_TOPICS}${NC}"

        # Show active topics
        echo -e "\nActive Topics:"
        docker exec crypto-viz-kafka kafka-topics --bootstrap-server localhost:9092 --list 2>/dev/null | while read topic; do
            echo -e "  ${CYAN}▸${NC} $topic"
        done
        echo ""

        echo -e "${BLUE}=== RESOURCE USAGE (Top 5) ===${NC}"
        echo -e "${CYAN}Container\t\t\tCPU\tMemory${NC}"
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep "crypto-viz" | head -5
        echo ""

        echo -e "${BLUE}=== ACCESS POINTS ===${NC}"
        echo -e "${GREEN}✓${NC} Frontend:        http://localhost:3000"
        echo -e "${GREEN}✓${NC} Backend API:     http://localhost:8000"
        echo -e "${GREEN}✓${NC} Kafka UI:        http://localhost:8085"
        echo -e "${GREEN}✓${NC} Spark UI:        http://localhost:8082"
        if docker ps | grep -q "crypto-viz-grafana"; then
            echo -e "${GREEN}✓${NC} Grafana:         http://localhost:3001 (admin/admin)"
            echo -e "${GREEN}✓${NC} Prometheus:      http://localhost:9090"
        else
            echo -e "${YELLOW}○${NC} Monitoring:      Run 'docker-compose -f monitoring/docker-compose.monitoring.yml up -d'"
        fi
        echo ""

        echo -e "${YELLOW}Press Ctrl+C to exit | Refreshing every 5 seconds...${NC}"
        sleep 5
    done
}

# Handle Ctrl+C
trap 'echo -e "\n${CYAN}Monitoring stopped${NC}"; exit 0' INT

# Start monitoring
monitor_loop
