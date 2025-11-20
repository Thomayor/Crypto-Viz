#!/bin/bash

# =====================================
# CRYPTO VIZ - Development Mode Script
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
echo "    CRYPTO VIZ - Development Mode"
echo "=================================================="
echo -e "${NC}"

# Create development override file
log "Creating development docker-compose override..."

cat > docker-compose.override.yml << 'EOF'
version: '3.8'

services:
  # Backend with hot reload
  backend:
    volumes:
      - ./backend:/app
    environment:
      - DEBUG=true
      - RELOAD=true
      - LOG_LEVEL=DEBUG
    command: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

  # Frontend with hot reload
  frontend:
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
    command: ["npm", "run", "serve"]
    ports:
      - "3000:8080"  # Vue dev server port

  # Analytics with code mounting
  analytics-builder:
    volumes:
      - ./services/analytics:/app
      - shared_data:/app/data
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG

  # Scraper with code mounting
  web-scraper:
    volumes:
      - ./services/scraper:/app
      - shared_data:/app/data
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - SCRAPER_INTERVAL=60  # Longer interval for dev

  # Development tools
  dev-tools:
    image: alpine:latest
    container_name: crypto-viz-dev-tools
    volumes:
      - ./:/workspace
      - shared_data:/app/data
    working_dir: /workspace
    command: tail -f /dev/null
    networks:
      - crypto-viz-network

  # Database admin tool
  duckdb-cli:
    image: python:3.11-slim
    container_name: crypto-viz-duckdb-cli
    volumes:
      - shared_data:/app/data
    working_dir: /app
    command: |
      sh -c "
        pip install duckdb &&
        tail -f /dev/null
      "
    networks:
      - crypto-viz-network

networks:
  crypto-viz-network:
    external: true
EOF

log "Development override created successfully"

# Start infrastructure services only
log "Starting infrastructure services for development..."
docker-compose up -d zookeeper kafka ollama spark-master spark-worker-1 spark-worker-2

# Wait for services
log "Waiting for infrastructure to be ready..."
sleep 30

# Check if user wants to start specific service
if [ $# -eq 0 ]; then
    echo ""
    echo "🛠️  Development environment ready!"
    echo ""
    echo "Available development commands:"
    echo "  ./scripts/dev.sh backend      # Start backend in dev mode"
    echo "  ./scripts/dev.sh frontend     # Start frontend in dev mode"
    echo "  ./scripts/dev.sh analytics    # Start analytics in dev mode"
    echo "  ./scripts/dev.sh scraper      # Start scraper in dev mode"
    echo "  ./scripts/dev.sh all          # Start all services"
    echo "  ./scripts/dev.sh logs         # Show all logs"
    echo "  ./scripts/dev.sh shell        # Get development shell"
    echo ""
    echo "Infrastructure services running:"
    echo "  • Kafka UI:        http://localhost:8081"
    echo "  • Spark Master UI: http://localhost:8080"
    echo "  • Ollama:          http://localhost:11434"
    echo ""
else
    case $1 in
        backend)
            log "Starting backend in development mode..."
            docker-compose up backend
            ;;
        frontend)
            log "Starting frontend in development mode..."
            docker-compose up frontend
            ;;
        analytics)
            log "Starting analytics in development mode..."
            docker-compose up analytics-builder
            ;;
        scraper)
            log "Starting scraper in development mode..."
            docker-compose up web-scraper
            ;;
        all)
            log "Starting all services in development mode..."
            docker-compose up backend frontend analytics-builder web-scraper
            ;;
        logs)
            log "Showing logs for all services..."
            docker-compose logs -f
            ;;
        shell)
            log "Starting development shell..."
            docker-compose exec dev-tools sh
            ;;
        duckdb)
            log "Starting DuckDB CLI..."
            docker-compose exec duckdb-cli python -c "
import duckdb
conn = duckdb.connect('/app/data/crypto_analytics.db')
print('DuckDB CLI - Connected to crypto_analytics.db')
print('Available tables:')
print(conn.execute('SHOW TABLES').fetchall())
print()
print('Enter SQL commands (type .quit to exit):')
while True:
    try:
        query = input('duckdb> ')
        if query.strip() == '.quit':
            break
        if query.strip():
            result = conn.execute(query).fetchall()
            for row in result:
                print(row)
    except Exception as e:
        print(f'Error: {e}')
conn.close()
"
            ;;
        *)
            echo "Unknown command: $1"
            echo "Use one of: backend, frontend, analytics, scraper, all, logs, shell, duckdb"
            exit 1
            ;;
    esac
fi