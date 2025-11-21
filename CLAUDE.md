# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CRYPTO VIZ** is a real-time cryptocurrency data analytics platform built with microservices architecture for an EPITECH MSc Pro project. It demonstrates modern data engineering practices using the required Bootstrap stack: **pandas**, **DuckDB**, and **Apache Spark**.

## Core Architecture

### Service Dependencies & Startup Order

Services must start in this sequence (handled by `scripts/start.sh`):
1. **Infrastructure**: Zookeeper → Kafka → Ollama → Spark Master → Spark Workers
2. **Data Pipeline**: Web Scraper → Analytics Builder
3. **Application**: Backend API → Frontend

The system is **event-driven** - all data flows through Kafka topics.

### Key Services

**Data Collection (`services/scraper/`)**
- Scrapes CoinGecko, NewsAPI, Reddit, Twitter
- Publishes to Kafka every 30s (prices), 5min (news), 10min (social)
- Configuration: `services/scraper/config/scraper_config.yaml`

**Analytics Engine (`services/analytics/`)**
- **Bootstrap stack integration** (required by EPITECH):
  - `pandas`: Data cleaning, chunking (10k rows), CSV processing
  - `DuckDB`: Fast analytics queries (2GB memory limit)
  - `Spark`: Distributed ML (LinearRegression, KMeans, IsolationForest)
- Sentiment analysis via Ollama (llama3.1:8b)
- Processes every 60s, batch analytics every 5min, ML retraining hourly
- Configuration: `services/analytics/config/analytics_config.yaml`

**Backend API (`backend/`)**
- FastAPI with WebSocket support for real-time updates
- Port 8000, docs at `/docs`
- Queries DuckDB, consumes Kafka analytics-data topic

**Frontend (`frontend/`)**
- Vue 3 + TypeScript + Vite
- Multi-stage Docker: Node build → Nginx production
- Port 3000

### Kafka Topics Architecture

Critical topics (see `kafka-config.yml`):
- `crypto-prices` (6 partitions, lz4, 30d retention) - High-throughput price data
- `crypto-news` (3 partitions, gzip, 7d retention) - News with sentiment
- `analytics-data` (3 partitions, snappy, 14d retention) - Processed analytics
- `alerts` (2 partitions, gzip, 3d retention) - System alerts
- Dead letter queues: `dlq-crypto-news`, `dlq-crypto-prices`

Created by: `./scripts/kafka-topics-setup.sh`

### Port Allocation

**Carefully chosen to avoid conflicts:**
- 3000: Frontend
- 8000: Backend API
- 8082: Spark Master UI (remapped from 8080)
- 8083-8084: Spark Workers
- 8085: Kafka UI
- 9092: Kafka (external), 29092 (internal)
- 11434: Ollama AI
- 2181: Zookeeper

**Monitoring (optional):**
- 3001: Grafana (admin/admin)
- 9090: Prometheus
- 9093: Alertmanager

## Essential Commands

### Setup & Startup
```bash
make install          # First-time setup: .env, directories, permissions
make quick-start      # Complete deployment: install + build + start
make start            # Start with intelligent sequencing
```

### Development
```bash
make dev              # Development mode (all services)
make dev-backend      # Backend with hot-reload
make dev-frontend     # Frontend with hot-reload
make dev-analytics    # Analytics with hot-reload
make dev-shell        # Interactive shell for debugging
```

### Monitoring & Debugging
```bash
make health           # Comprehensive health check
make logs             # All service logs
make logs-backend     # Backend-specific logs
make logs-kafka       # Kafka logs
make logs-analytics   # Analytics engine logs
make duckdb           # DuckDB CLI for querying analytics
make kafka-topics     # List Kafka topics and their state
```

### Testing
```bash
make test             # Run all tests
make test-backend     # Backend tests only
make test-analytics   # Analytics tests only
```

### Infrastructure Access
```bash
make kafka-ui         # Open Kafka UI (localhost:8085)
make spark-ui         # Open Spark UI (localhost:8082)
make urls             # Show all service URLs
```

### Cleanup
```bash
make restart          # Restart services
make restart-clean    # Restart with volume cleanup
make clean            # Clean containers and images
make clean-all        # Complete cleanup (⚠️ DATA LOSS)
```

## Configuration Files

**Environment Variables**: `.env` (create from `.env.example`)
- API keys: `NEWS_API_KEY`, `COINGECKO_API_KEY`
- Service intervals: `SCRAPER_INTERVAL`, `ANALYTICS_INTERVAL`
- Ollama model: `OLLAMA_MODEL=llama3.1:8b`

**Service Configs**:
- `services/scraper/config/scraper_config.yaml` - API endpoints, scraping intervals, rate limits
- `services/analytics/config/analytics_config.yaml` - Bootstrap stack settings, ML models, alerting rules
- `kafka-config.yml` - Topics, partitions, retention, producers/consumers

**Docker**:
- `docker-compose.yml` - Main infrastructure (14 services)
- `monitoring/docker-compose.monitoring.yml` - Optional observability stack

**Database**:
- `database/init/01_schema.sql` - **Auto-applied** PostgreSQL schema (executed on first startup)
  - Includes: `analysis_method`, `confidence_score` (crypto_news), `circulating_supply`, `total_supply`, `max_supply` (crypto_prices)
- `database/migrations/` - Historical migrations (now integrated into init schema, **no longer auto-executed**)
- `database/schema.sql` - Reference schema documentation

**Important**: Database schema is automatically initialized when PostgreSQL starts. No manual migration needed! The old migration system (`migrate_db.py`) has been disabled to prevent conflicts with auto-initialization.

## Critical Architectural Patterns

### Bootstrap Stack Integration (EPITECH Requirement)

All three technologies are integrated in `services/analytics/`:

**pandas** - Data manipulation
```python
# Chunked processing for memory efficiency
chunk_size = 10000
for chunk in pd.read_csv(..., chunksize=chunk_size):
    # Process data
```

**DuckDB** - Analytical queries
```python
# Fast aggregations and time-series queries
con = duckdb.connect('crypto_analytics.db')
con.execute("SELECT * FROM prices WHERE timestamp > ?", [cutoff])
```

**Spark** - Distributed ML
```python
# Price prediction, clustering, anomaly detection
from pyspark.ml.regression import LinearRegression
from pyspark.ml.clustering import KMeans
from pyspark.ml.feature import IsolationForest
```

Configuration in `analytics_config.yaml` under `bootstrap_stack` section.

### Health Checks

All services have Docker health checks with:
- `start_period`: Grace period for initialization (30s-300s depending on service)
- `interval`: Check frequency (30s-120s)
- `retries`: Failure tolerance before marking unhealthy

Check via: `docker ps` or `make health`

### Data Persistence

**Shared Volumes** (critical - do not delete in production):
- `postgres_data`: PostgreSQL database (schema auto-initialized from `database/init/`)
- `shared_data`: Analytics ↔ Backend data exchange
- `duckdb_data`: DuckDB database files
- `kafka_data`: Kafka topics (persistent)
- `ollama_data`: LLM models (~4.7GB)
- `spark_data`: Spark checkpoints

**Database Initialization**: On first startup (or after `docker-compose down -v`), PostgreSQL automatically executes `database/init/01_schema.sql` to create all tables, indexes, and seed data. Includes `analysis_method` and `confidence_score` columns in `crypto_news`.

### Error Handling

**Scraper**: Rate limiting, circuit breakers, exponential backoff, dead letter queues
**Analytics**: Data validation, error logging to `system-logs` topic
**Kafka**: Automatic topic creation, replication factor 1 (single broker)

### Networking

All services in `crypto-viz-network`:
- Internal communication: Use service names (`kafka:29092`, `ollama:11434`)
- External access: Use `localhost` with mapped ports
- Kafka advertised listeners configured for both

## Development Workflow

### First-Time Setup
1. `make install` - Creates .env, directories
2. Add API keys to .env (optional - demo mode works without)
3. `make quick-start` - Builds and starts everything (~5-10 min first time)
4. Wait for all health checks to pass
5. Access http://localhost:3000

### Making Changes

**Backend/Analytics/Scraper** (Python):
1. Modify code in respective directory
2. `make restart-[service]` or use `make dev-[service]` for hot-reload
3. Check logs: `make logs-[service]`

**Frontend** (Vue.js):
1. Modify code in `frontend/src/`
2. `make dev-frontend` for hot-reload
3. Or `make restart-frontend` after changes

**Configuration changes**:
1. Modify YAML configs
2. `make restart-full` to rebuild and restart

### Debugging

**Check service health**: `make health` or `docker ps`
**View logs**: `make logs-[service]`
**Query database**: `make duckdb`
**Check Kafka**: `make kafka-topics` or open Kafka UI
**ML model inspection**: `make spark-ui`
**Interactive debugging**: `make dev-shell`

### Testing

Run tests before committing:
```bash
make test              # All tests
make test-backend      # Backend only
make test-analytics    # Analytics only
```

## Monitoring Stack (Optional)

Start with: `docker-compose -f monitoring/docker-compose.monitoring.yml up -d`

Services:
- **Prometheus** (9090): Metrics collection from all services
- **Grafana** (3001): Dashboards - manually configure Prometheus datasource at http://prometheus:9090
- **Alertmanager** (9093): Alert routing
- **cAdvisor** (8086): Container metrics
- **Node Exporter** (9100): System metrics

**Note**: Loki (log aggregation) may have startup issues - Prometheus alone is sufficient for core monitoring.

Scripts:
- `scripts/start-monitoring.sh` - Start monitoring stack
- `scripts/monitoring-dashboard.sh` - CLI dashboard
- `scripts/validate-monitoring.py` - Verify configuration

## Important Notes

### Kafka Topics

Topics are created automatically on first message OR manually via:
```bash
./scripts/kafka-topics-setup.sh
```

Topic naming convention: `{source}-{type}` (e.g., `crypto-prices`, `analytics-data`)

### Ollama Model

First startup downloads llama3.1:8b (~4.7GB). This takes time.
Check progress: `docker logs crypto-viz-ollama`

If model isn't loaded:
```bash
docker exec crypto-viz-ollama ollama pull llama3.1:8b
```

### Spark Cluster

Spark Master must start before workers. The `scripts/start.sh` handles this.
Workers auto-connect to `spark://spark-master:7077`

### DuckDB

Database location: `/app/data/crypto_analytics.db` (in `shared_data` volume)
Access via: `make duckdb` or Python client in analytics/backend

### Performance

**Minimum**: 8GB RAM, 10GB disk
**Recommended**: 16GB RAM, 20GB disk
All services can run on a single machine but scaling is possible via Docker Swarm/Kubernetes.

### Security

- Services run as non-root users
- CORS configured for frontend
- JWT authentication supported (not implemented by default)
- No secrets in Docker images - use .env

## Troubleshooting

**Services won't start**:
- Check `make health` output
- Verify ports not in use: `netstat -an | findstr "8000 3000 9092"`
- Check Docker daemon running

**Kafka connection errors**:
- Ensure Zookeeper started first
- Check `docker logs crypto-viz-kafka`
- Verify network: `docker network ls | grep crypto-viz`

**Ollama not responding**:
- Model download may be in progress (check logs)
- Restart: `docker-compose restart ollama`

**Analytics not processing**:
- Check Kafka topics exist: `make kafka-topics`
- Verify scraper is publishing: `make logs-scraper`
- Check DuckDB: `make duckdb`

**Frontend won't load**:
- Backend must be running first
- Check CORS settings in backend
- Verify WebSocket connection in browser console

## Project Structure Reference

```
.
├── backend/              # FastAPI application
├── frontend/             # Vue 3 + TypeScript SPA
├── services/
│   ├── scraper/         # Data collection service
│   └── analytics/       # Bootstrap stack integration + ML
├── scripts/             # Management automation
├── monitoring/          # Observability stack (optional)
├── kafka-config.yml     # Kafka topics configuration
├── docker-compose.yml   # Main infrastructure
├── Makefile            # Command shortcuts
└── .env                # Environment variables (create from .env.example)
```

## Getting Help

- **Health issues**: `make health` provides comprehensive status
- **Logs**: `make logs-[service]` for specific service logs
- **Service URLs**: `make urls` shows all access points
- **API docs**: http://localhost:8000/docs (Swagger/OpenAPI)
- **Kafka state**: Kafka UI at http://localhost:8085
