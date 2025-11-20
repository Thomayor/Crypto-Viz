#!/bin/bash

# =====================================
# CRYPTO VIZ - Scraper Entrypoint
# =====================================

set -e

echo "=== CRYPTO VIZ WEB SCRAPER STARTING ==="

# Fonction de logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Vérification des variables d'environnement requises
log "Checking environment variables..."

# Variables Kafka (requises)
: ${KAFKA_BOOTSTRAP_SERVERS:?"KAFKA_BOOTSTRAP_SERVERS is required"}

# Variables API (optionnelles avec avertissement)
if [ -z "$NEWS_API_KEY" ]; then
    log "WARNING: NEWS_API_KEY not set, news scraping will be disabled"
fi

if [ -z "$COINGECKO_API_KEY" ]; then
    log "WARNING: COINGECKO_API_KEY not set, using free tier (rate limited)"
fi

# Créer les répertoires nécessaires
mkdir -p /app/data/scraping
mkdir -p /app/logs

# Attente de Kafka (avec retry)
log "Waiting for Kafka to be ready..."
wait_for_kafka() {
    local retries=30
    local count=0
    
    while [ $count -lt $retries ]; do
        if python -c "
from kafka import KafkaProducer
import sys
try:
    producer = KafkaProducer(
        bootstrap_servers='$KAFKA_BOOTSTRAP_SERVERS',
        request_timeout_ms=5000,
        api_version_auto_timeout_ms=5000
    )
    producer.close()
    sys.exit(0)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; then
            log "Kafka is ready!"
            return 0
        fi
        
        count=$((count + 1))
        log "Kafka not ready yet (attempt $count/$retries), waiting 10s..."
        sleep 10
    done
    
    log "ERROR: Kafka failed to become ready within timeout"
    return 1
}

wait_for_kafka || exit 1

# Créer les topics Kafka s'ils n'existent pas
log "Creating Kafka topics..."
python - <<EOF
import sys
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import logging

logging.basicConfig(level=logging.INFO)

try:
    admin_client = KafkaAdminClient(
        bootstrap_servers='$KAFKA_BOOTSTRAP_SERVERS',
        request_timeout_ms=10000
    )
    
    topics = [
        NewTopic(name='crypto-news', num_partitions=3, replication_factor=1),
        NewTopic(name='crypto-prices', num_partitions=3, replication_factor=1),
        NewTopic(name='social-posts', num_partitions=3, replication_factor=1),
        NewTopic(name='analytics-data', num_partitions=3, replication_factor=1),
        NewTopic(name='alerts', num_partitions=1, replication_factor=1)
    ]
    
    for topic in topics:
        try:
            admin_client.create_topics([topic])
            print(f"Created topic: {topic.name}")
        except TopicAlreadyExistsError:
            print(f"Topic already exists: {topic.name}")
        except Exception as e:
            print(f"Error creating topic {topic.name}: {e}")
    
    admin_client.close()
    print("Kafka topics setup completed!")
    
except Exception as e:
    print(f"Error setting up Kafka topics: {e}")
    sys.exit(1)
EOF

# Démarrage du serveur de health check en arrière-plan
log "Starting health check server..."
python - <<EOF &
import uvicorn
from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "crypto-viz-scraper",
        "version": "1.0"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")
EOF

HEALTH_PID=$!
log "Health check server started with PID: $HEALTH_PID"

# Fonction de nettoyage
cleanup() {
    log "Shutting down gracefully..."
    if [ ! -z "$HEALTH_PID" ]; then
        kill $HEALTH_PID 2>/dev/null || true
    fi
    exit 0
}

# Gestion des signaux
trap cleanup SIGINT SIGTERM

# Test de connectivité vers les APIs externes
log "Testing external API connectivity..."

# Test CoinGecko
if curl -s --max-time 10 "https://api.coingecko.com/api/v3/ping" > /dev/null; then
    log "✓ CoinGecko API accessible"
else
    log "⚠ CoinGecko API not accessible (may impact price scraping)"
fi

# Test NewsAPI si configuré
if [ ! -z "$NEWS_API_KEY" ]; then
    if curl -s --max-time 10 "https://newsapi.org/v2/everything?q=bitcoin&apiKey=$NEWS_API_KEY&pageSize=1" > /dev/null; then
        log "✓ NewsAPI accessible"
    else
        log "⚠ NewsAPI not accessible (may impact news scraping)"
    fi
fi

log "Pre-flight checks completed!"
log "Starting main scraper process..."

# Execute the CMD (Python script)
exec "$@"