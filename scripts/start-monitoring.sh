#!/bin/bash

# =====================================
# CRYPTO VIZ - Start Monitoring Stack
# =====================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Starting Crypto Viz Monitoring Infrastructure             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if main services are running
echo -e "${YELLOW}Checking main services...${NC}"
if ! docker ps | grep -q "crypto-viz-kafka"; then
    echo -e "${YELLOW}⚠ Main services not running. Starting them first...${NC}"
    docker-compose up -d zookeeper kafka
    echo -e "${YELLOW}Waiting for Kafka to be ready (60s)...${NC}"
    sleep 60
fi

echo -e "${GREEN}✓ Main services are running${NC}"
echo ""

# Create network if it doesn't exist
if ! docker network ls | grep -q "crypto-viz-network"; then
    echo -e "${YELLOW}Creating crypto-viz-network...${NC}"
    docker network create crypto-viz-network
fi

# Start monitoring stack
echo -e "${BLUE}Starting monitoring services...${NC}"
cd "$(dirname "$0")/.."
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

echo ""
echo -e "${YELLOW}Waiting for services to start (30s)...${NC}"
sleep 30

# Check service status
echo ""
echo -e "${BLUE}=== Monitoring Services Status ===${NC}"
docker-compose -f monitoring/docker-compose.monitoring.yml ps

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Monitoring Stack Started Successfully!                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}=== Access Points ===${NC}"
echo -e "${GREEN}✓${NC} Grafana Dashboard:   ${YELLOW}http://localhost:3001${NC} (admin/admin)"
echo -e "${GREEN}✓${NC} Prometheus:          ${YELLOW}http://localhost:9090${NC}"
echo -e "${GREEN}✓${NC} Alertmanager:        ${YELLOW}http://localhost:9093${NC}"
echo -e "${GREEN}✓${NC} Kafka Exporter:      ${YELLOW}http://localhost:9308/metrics${NC}"
echo -e "${GREEN}✓${NC} Node Exporter:       ${YELLOW}http://localhost:9100/metrics${NC}"
echo -e "${GREEN}✓${NC} cAdvisor:            ${YELLOW}http://localhost:8086${NC}"
echo ""
echo -e "${BLUE}=== Next Steps ===${NC}"
echo -e "1. Open Grafana: ${YELLOW}http://localhost:3001${NC}"
echo -e "2. Login with: ${YELLOW}admin/admin${NC}"
echo -e "3. Navigate to Dashboards → Crypto Visualization → System Overview"
echo -e "4. Run: ${YELLOW}./scripts/monitoring-dashboard.sh${NC} for CLI monitoring"
echo ""
echo -e "${BLUE}=== Useful Commands ===${NC}"
echo -e "View logs:        ${YELLOW}docker-compose -f monitoring/docker-compose.monitoring.yml logs -f [service]${NC}"
echo -e "Stop monitoring:  ${YELLOW}docker-compose -f monitoring/docker-compose.monitoring.yml down${NC}"
echo -e "Restart service:  ${YELLOW}docker-compose -f monitoring/docker-compose.monitoring.yml restart [service]${NC}"
echo ""
