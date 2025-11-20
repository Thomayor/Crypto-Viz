#!/bin/bash

# =====================================
# CRYPTO VIZ - VM Deployment Script
# =====================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VM_HOST="${VM_HOST:-84.235.229.76}"
VM_USER="${VM_USER:-ubuntu}"
DEPLOY_DIR="crypto-viz"

echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}CRYPTO VIZ - VM Deployment${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""
echo "Target VM: ${VM_USER}@${VM_HOST}"
echo "Deploy directory: ~/${DEPLOY_DIR}"
echo ""

# Check SSH connection
echo -e "${YELLOW}→ Testing SSH connection...${NC}"
if ssh -o ConnectTimeout=5 ${VM_USER}@${VM_HOST} "echo 'Connection successful'" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ SSH connection successful${NC}"
else
    echo -e "${RED}❌ Cannot connect to VM via SSH${NC}"
    echo "Please ensure:"
    echo "  1. SSH key is added to ssh-agent"
    echo "  2. Public key is in ~/.ssh/authorized_keys on the VM"
    echo "  3. VM_HOST and VM_USER are correct"
    exit 1
fi

# Create deployment directory
echo -e "${YELLOW}→ Creating deployment directory...${NC}"
ssh ${VM_USER}@${VM_HOST} "mkdir -p ~/${DEPLOY_DIR}"

# Copy docker-compose.prod.yml
echo -e "${YELLOW}→ Copying docker-compose.prod.yml...${NC}"
scp docker-compose.prod.yml ${VM_USER}@${VM_HOST}:~/${DEPLOY_DIR}/docker-compose.yml

# Copy kafka-config.yml
echo -e "${YELLOW}→ Copying kafka-config.yml...${NC}"
scp kafka-config.yml ${VM_USER}@${VM_HOST}:~/${DEPLOY_DIR}/

# Copy .env.production
echo -e "${YELLOW}→ Copying .env.production...${NC}"
scp .env.production ${VM_USER}@${VM_HOST}:~/${DEPLOY_DIR}/.env

# Deploy on VM
echo -e "${YELLOW}→ Deploying on VM...${NC}"
ssh ${VM_USER}@${VM_HOST} << 'ENDSSH'
cd ~/crypto-viz

echo "=== Checking Docker installation ==="
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Installing..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "Docker installed. Please log out and back in, then run this script again."
    exit 0
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose not found. Installing..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo "=== Docker version ==="
docker --version
docker-compose --version

echo ""
echo "=== Stopping existing services ==="
docker-compose down 2>/dev/null || true

echo ""
echo "=== Pulling latest images ==="
docker-compose pull

echo ""
echo "=== Starting services ==="
docker-compose up -d

echo ""
echo "=== Waiting for services to start ==="
sleep 30

echo ""
echo "=== Service status ==="
docker-compose ps

echo ""
echo "=== Checking logs ==="
docker-compose logs --tail=50

ENDSSH

echo ""
echo -e "${GREEN}=================================${NC}"
echo -e "${GREEN}✅ Deployment completed!${NC}"
echo -e "${GREEN}=================================${NC}"
echo ""
echo "Service URLs:"
echo "  Frontend:  http://${VM_HOST}:3000"
echo "  Backend:   http://${VM_HOST}:8000"
echo "  API Docs:  http://${VM_HOST}:8000/docs"
echo "  Kafka UI:  http://${VM_HOST}:8085"
echo "  Spark UI:  http://${VM_HOST}:8082"
echo ""
echo "To view logs:"
echo "  ssh ${VM_USER}@${VM_HOST} 'cd ${DEPLOY_DIR} && docker-compose logs -f'"
echo ""
echo "To restart services:"
echo "  ssh ${VM_USER}@${VM_HOST} 'cd ${DEPLOY_DIR} && docker-compose restart'"
