#!/bin/bash

# =====================================
# CRYPTO VIZ - Validate Monitoring Setup
# =====================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Validating Monitoring Configuration                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

VALIDATION_PASSED=true

# Check if monitoring files exist
echo -e "${BLUE}=== Checking Configuration Files ===${NC}"

FILES=(
    "monitoring/docker-compose.monitoring.yml"
    "monitoring/prometheus/prometheus.yml"
    "monitoring/prometheus/alerts.yml"
    "monitoring/prometheus/alertmanager.yml"
    "monitoring/loki/loki-config.yml"
    "monitoring/loki/promtail-config.yml"
    "monitoring/grafana/provisioning/datasources/datasources.yml"
    "monitoring/grafana/provisioning/dashboards/dashboards.yml"
    "monitoring/grafana/dashboards/crypto-viz-overview.json"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file - Missing!"
        VALIDATION_PASSED=false
    fi
done

echo ""
echo -e "${BLUE}=== Checking Scripts ===${NC}"

SCRIPTS=(
    "scripts/health-check.sh"
    "scripts/monitoring-dashboard.sh"
    "scripts/start-monitoring.sh"
    "scripts/validate-monitoring.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        echo -e "${GREEN}✓${NC} $script (executable)"
    elif [ -f "$script" ]; then
        echo -e "${YELLOW}⚠${NC} $script (not executable - fixing...)"
        chmod +x "$script"
        echo -e "${GREEN}✓${NC} $script (fixed)"
    else
        echo -e "${RED}✗${NC} $script - Missing!"
        VALIDATION_PASSED=false
    fi
done

echo ""
echo -e "${BLUE}=== Validating Docker Compose Syntax ===${NC}"

if docker-compose -f monitoring/docker-compose.monitoring.yml config > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} docker-compose.monitoring.yml syntax is valid"
else
    echo -e "${RED}✗${NC} docker-compose.monitoring.yml syntax error"
    VALIDATION_PASSED=false
fi

echo ""
echo -e "${BLUE}=== Checking Required Directories ===${NC}"

DIRS=(
    "monitoring/prometheus"
    "monitoring/grafana/provisioning/datasources"
    "monitoring/grafana/provisioning/dashboards"
    "monitoring/grafana/dashboards"
    "monitoring/loki"
)

for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $dir"
    else
        echo -e "${RED}✗${NC} $dir - Missing!"
        VALIDATION_PASSED=false
    fi
done

echo ""
echo -e "${BLUE}=== Checking Network ===${NC}"

if docker network ls | grep -q "crypto-viz-network"; then
    echo -e "${GREEN}✓${NC} crypto-viz-network exists"
else
    echo -e "${YELLOW}⚠${NC} crypto-viz-network doesn't exist yet (will be created)"
fi

echo ""
echo -e "${BLUE}=== Testing Monitoring Services (if running) ===${NC}"

# Check if monitoring is running
if docker ps | grep -q "crypto-viz-prometheus"; then
    echo -e "${GREEN}✓${NC} Monitoring stack is running"
    echo ""

    # Test Prometheus
    if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Prometheus is healthy"
    else
        echo -e "${RED}✗${NC} Prometheus is not responding"
    fi

    # Test Grafana
    if curl -s http://localhost:3001/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Grafana is healthy"
    else
        echo -e "${RED}✗${NC} Grafana is not responding"
    fi

    # Test Loki
    if curl -s http://localhost:3100/ready > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Loki is ready"
    else
        echo -e "${RED}✗${NC} Loki is not responding"
    fi

    # Check Prometheus targets
    TARGETS=$(curl -s http://localhost:9090/api/v1/targets 2>/dev/null | grep -o '"health":"up"' | wc -l)
    echo -e "${GREEN}✓${NC} Prometheus has $TARGETS targets up"

else
    echo -e "${YELLOW}⚠${NC} Monitoring stack is not running"
    echo "  To start: ./scripts/start-monitoring.sh"
fi

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
if [ "$VALIDATION_PASSED" = true ]; then
    echo -e "║ ${GREEN}✓ Validation PASSED${NC}                                           ║"
    echo "║                                                                ║"
    echo "║ All monitoring configuration files are in place!               ║"
    echo "║                                                                ║"
    echo "║ Next steps:                                                    ║"
    echo "║ 1. Start monitoring: ./scripts/start-monitoring.sh            ║"
    echo "║ 2. Access Grafana:   http://localhost:3001 (admin/admin)      ║"
    echo "║ 3. CLI Dashboard:    ./scripts/monitoring-dashboard.sh        ║"
else
    echo -e "║ ${RED}✗ Validation FAILED${NC}                                           ║"
    echo "║                                                                ║"
    echo "║ Some configuration files are missing or invalid.               ║"
    echo "║ Please check the errors above.                                 ║"
fi
echo "╚════════════════════════════════════════════════════════════════╝"

exit $([ "$VALIDATION_PASSED" = true ] && echo 0 || echo 1)
