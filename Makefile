# =====================================
# CRYPTO VIZ - Makefile
# =====================================

.PHONY: help install start stop restart health dev clean logs build test

# Default target
.DEFAULT_GOAL := help

# Colors for output
GREEN  := \033[0;32m
YELLOW := \033[1;33m
BLUE   := \033[0;34m
RED    := \033[0;31m
NC     := \033[0m # No Color

# Project variables
PROJECT_NAME := crypto-viz
COMPOSE_FILE := docker-compose.yml
ENV_FILE := .env

##@ Help
help: ## Display this help message
	@echo -e "$(BLUE)"
	@echo "=================================================="
	@echo "    CRYPTO VIZ - Docker Compose Management"
	@echo "=================================================="
	@echo -e "$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(GREEN)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup and Installation
install: ## Initial setup - copy .env.example to .env and make scripts executable
	@echo -e "$(BLUE)Setting up CRYPTO VIZ environment...$(NC)"
	@if [ ! -f $(ENV_FILE) ]; then \
		cp .env.example $(ENV_FILE); \
		echo -e "$(GREEN)✅ Created $(ENV_FILE) from .env.example$(NC)"; \
		echo -e "$(YELLOW)⚠️  Please configure your API keys in $(ENV_FILE)$(NC)"; \
	else \
		echo -e "$(YELLOW)$(ENV_FILE) already exists$(NC)"; \
	fi
	@chmod +x scripts/*.sh
	@echo -e "$(GREEN)✅ Made scripts executable$(NC)"
	@mkdir -p data/{analytics,parquet,scraping} logs
	@echo -e "$(GREEN)✅ Created necessary directories$(NC)"

##@ Docker Operations
build: ## Build all Docker images
	@echo -e "$(BLUE)Building Docker images...$(NC)"
	@docker-compose build --parallel
	@echo -e "$(GREEN)✅ Docker images built successfully$(NC)"

start: ## Start all services
	@echo -e "$(BLUE)Starting CRYPTO VIZ services...$(NC)"
	@./scripts/start.sh
	@echo -e "$(BLUE)Applying ML Analytics schema...$(NC)"
	@bash ./scripts/apply_ml_schema.sh || true

stop: ## Stop all services
	@echo -e "$(BLUE)Stopping CRYPTO VIZ services...$(NC)"
	@./scripts/stop.sh

restart: ## Restart all services
	@echo -e "$(BLUE)Restarting CRYPTO VIZ services...$(NC)"
	@./scripts/restart.sh

restart-clean: ## Restart with clean volumes
	@echo -e "$(BLUE)Restarting with clean volumes...$(NC)"
	@./scripts/restart.sh --clean

restart-full: ## Full restart (rebuild + clean)
	@echo -e "$(BLUE)Full restart (rebuild + clean)...$(NC)"
	@./scripts/restart.sh --full

##@ Development
dev: ## Start development environment
	@echo -e "$(BLUE)Starting development environment...$(NC)"
	@./scripts/dev.sh

dev-backend: ## Start backend in development mode
	@./scripts/dev.sh backend

dev-frontend: ## Start frontend in development mode
	@./scripts/dev.sh frontend

dev-analytics: ## Start analytics in development mode
	@./scripts/dev.sh analytics

dev-scraper: ## Start scraper in development mode
	@./scripts/dev.sh scraper

dev-all: ## Start all services in development mode
	@./scripts/dev.sh all

dev-shell: ## Get development shell
	@./scripts/dev.sh shell

##@ Monitoring and Debugging
health: ## Check system health
	@./scripts/health-check.sh

logs: ## Show logs for all services
	@docker-compose logs -f

logs-backend: ## Show backend logs
	@docker-compose logs -f backend

logs-frontend: ## Show frontend logs
	@docker-compose logs -f frontend

logs-analytics: ## Show analytics logs
	@docker-compose logs -f analytics-builder

logs-scraper: ## Show scraper logs
	@docker-compose logs -f web-scraper

logs-kafka: ## Show kafka logs
	@docker-compose logs -f kafka

logs-ollama: ## Show ollama logs
	@docker-compose logs -f ollama

status: ## Show container status
	@echo -e "$(BLUE)Container Status:$(NC)"
	@docker-compose ps
	@echo ""
	@echo -e "$(BLUE)Resource Usage:$(NC)"
	@docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

##@ Database and Analytics
duckdb: ## Connect to DuckDB CLI
	@./scripts/dev.sh duckdb

kafka-topics: ## List Kafka topics
	@echo -e "$(BLUE)Kafka Topics:$(NC)"
	@docker exec crypto-viz-kafka kafka-topics --bootstrap-server localhost:9092 --list

kafka-ui: ## Open Kafka UI in browser
	@echo -e "$(BLUE)Opening Kafka UI...$(NC)"
	@echo "Kafka UI available at: http://localhost:8085"
	@command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:8085 || \
	 command -v open >/dev/null 2>&1 && open http://localhost:8085 || \
	 echo "Please open http://localhost:8085 in your browser"

spark-ui: ## Open Spark UI in browser
	@echo -e "$(BLUE)Opening Spark UI...$(NC)"
	@echo "Spark UI available at: http://localhost:8082"
	@command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:8082 || \
	 command -v open >/dev/null 2>&1 && open http://localhost:8082 || \
	 echo "Please open http://localhost:8082 in your browser"

##@ Testing
test: ## Run all tests
	@echo -e "$(BLUE)Running tests...$(NC)"
	@docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
	@docker-compose -f docker-compose.test.yml down

test-backend: ## Run backend tests only
	@echo -e "$(BLUE)Running backend tests...$(NC)"
	@docker-compose exec backend python -m pytest tests/ -v

test-analytics: ## Run analytics tests only
	@echo -e "$(BLUE)Running analytics tests...$(NC)"
	@docker-compose exec analytics-builder python -m pytest tests/ -v

##@ Cleanup
clean: ## Clean up containers, networks, and dangling images
	@echo -e "$(BLUE)Cleaning up Docker resources...$(NC)"
	@docker-compose down --remove-orphans
	@docker system prune -f
	@echo -e "$(GREEN)✅ Cleanup completed$(NC)"

clean-all: ## Clean everything including volumes and images
	@echo -e "$(RED)WARNING: This will remove ALL data and images!$(NC)"
	@echo -e "$(YELLOW)Press Ctrl+C to cancel, or Enter to continue...$(NC)"
	@read
	@./scripts/stop.sh --all
	@docker system prune -a -f --volumes
	@echo -e "$(GREEN)✅ Complete cleanup finished$(NC)"

clean-volumes: ## Remove only volumes (data loss!)
	@echo -e "$(RED)WARNING: This will remove ALL persisted data!$(NC)"
	@echo -e "$(YELLOW)Press Ctrl+C to cancel, or Enter to continue...$(NC)"
	@read
	@./scripts/stop.sh --volumes
	@echo -e "$(GREEN)✅ Volumes cleaned$(NC)"

##@ Utilities
ps: ## Show running containers
	@docker-compose ps

top: ## Show running processes in containers
	@docker-compose top

pull: ## Pull latest images
	@echo -e "$(BLUE)Pulling latest images...$(NC)"
	@docker-compose pull
	@echo -e "$(GREEN)✅ Images updated$(NC)"

config: ## Validate and show docker-compose configuration
	@docker-compose config

open: ## Open the application in browser
	@echo -e "$(BLUE)Opening CRYPTO VIZ application...$(NC)"
	@echo "Application available at: http://localhost:3000"
	@command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:3000 || \
	 command -v open >/dev/null 2>&1 && open http://localhost:3000 || \
	 echo "Please open http://localhost:3000 in your browser"

##@ Environment Management
env-check: ## Check environment configuration
	@echo -e "$(BLUE)Checking environment configuration...$(NC)"
	@if [ -f $(ENV_FILE) ]; then \
		echo -e "$(GREEN)✅ $(ENV_FILE) exists$(NC)"; \
		echo -e "$(BLUE)Required variables:$(NC)"; \
		grep -E "^[A-Z_]+=.*$$" $(ENV_FILE) | head -10; \
		echo "..."; \
	else \
		echo -e "$(RED)❌ $(ENV_FILE) not found$(NC)"; \
		echo -e "$(YELLOW)Run 'make install' first$(NC)"; \
	fi

env-template: ## Regenerate .env from .env.example
	@echo -e "$(YELLOW)Regenerating $(ENV_FILE) from template...$(NC)"
	@cp .env.example $(ENV_FILE)
	@echo -e "$(GREEN)✅ $(ENV_FILE) regenerated$(NC)"
	@echo -e "$(YELLOW)⚠️  Please reconfigure your API keys$(NC)"

##@ Quick Actions
quick-start: install build start ## Complete setup and start (install + build + start)

quick-reset: stop clean-volumes start ## Quick reset with data cleanup

demo: ## Start with demo/sample data
	@echo -e "$(BLUE)Starting CRYPTO VIZ in demo mode...$(NC)"
	@echo "DEMO_MODE=true" >> $(ENV_FILE)
	@make start
	@echo -e "$(GREEN)✅ Demo mode started$(NC)"
	@echo "Dashboard: http://localhost:3000"

##@ Documentation
urls: ## Show all service URLs
	@echo -e "$(BLUE)CRYPTO VIZ Service URLs:$(NC)"
	@echo "📊 Main Dashboard:     http://localhost:3000"
	@echo "🔧 Backend API:        http://localhost:8000"
	@echo "📈 API Documentation:  http://localhost:8000/docs"
	@echo "🔍 Kafka UI:           http://localhost:8085"
	@echo "⚡ Spark Master UI:    http://localhost:8082"
	@echo "🔧 Spark Worker 1:     http://localhost:8083"
	@echo "🔧 Spark Worker 2:     http://localhost:8084"
	@echo "🤖 Ollama API:         http://localhost:11434"
	@echo ""
	@echo -e "$(BLUE)Health Check Endpoints:$(NC)"
	@echo "🏥 Backend Health:     http://localhost:8000/health"
	@echo "🏥 Frontend Health:    http://localhost:3000/health"

version: ## Show version information
	@echo -e "$(BLUE)CRYPTO VIZ Version Information:$(NC)"
	@echo "Project: $(PROJECT_NAME)"
	@echo "Docker Compose: $(shell docker-compose version --short)"
	@echo "Docker: $(shell docker version --format '{{.Client.Version}}')"
	@echo ""
	@echo -e "$(BLUE)Service Images:$(NC)"
	@docker-compose config --services | while read service; do \
		image=$$(docker-compose config | grep -A 5 "$$service:" | grep "image:" | awk '{print $$2}'); \
		if [ ! -z "$$image" ]; then \
			echo "$$service: $$image"; \
		fi; \
	done

##@ Production Deployment
deploy: ## Deploy to production VM (requires SSH access)
	@echo -e "$(BLUE)Deploying to production VM...$(NC)"
	@chmod +x scripts/deploy-to-vm.sh
	@./scripts/deploy-to-vm.sh

deploy-check: ## Check production deployment status
	@echo -e "$(BLUE)Checking production VM status...$(NC)"
	@ssh ubuntu@84.235.229.76 'cd ~/crypto-viz && docker-compose ps'

deploy-logs: ## Show production logs
	@echo -e "$(BLUE)Fetching production logs...$(NC)"
	@ssh ubuntu@84.235.229.76 'cd ~/crypto-viz && docker-compose logs --tail=100'

deploy-restart: ## Restart production services
	@echo -e "$(BLUE)Restarting production services...$(NC)"
	@ssh ubuntu@84.235.229.76 'cd ~/crypto-viz && docker-compose restart'

deploy-down: ## Stop production services
	@echo -e "$(YELLOW)Stopping production services...$(NC)"
	@ssh ubuntu@84.235.229.76 'cd ~/crypto-viz && docker-compose down'

deploy-up: ## Start production services
	@echo -e "$(BLUE)Starting production services...$(NC)"
	@ssh ubuntu@84.235.229.76 'cd ~/crypto-viz && docker-compose up -d'

prod-urls: ## Show production URLs
	@echo -e "$(BLUE)CRYPTO VIZ Production URLs:$(NC)"
	@echo "📊 Frontend:       http://84.235.229.76:3000"
	@echo "🔧 Backend API:    http://84.235.229.76:8000"
	@echo "📈 API Docs:       http://84.235.229.76:8000/docs"
	@echo "🔍 Kafka UI:       http://84.235.229.76:8085"
	@echo "⚡ Spark UI:       http://84.235.229.76:8082"