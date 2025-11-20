#!/bin/bash

# =====================================
# CRYPTO VIZ - Analytics Entrypoint
# =====================================

set -e

echo "=== CRYPTO VIZ ANALYTICS SERVICE STARTING ==="

# Fonction de logging
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Vérification des variables d'environnement requises
log "Checking environment variables..."

: ${KAFKA_BOOTSTRAP_SERVERS:?"KAFKA_BOOTSTRAP_SERVERS is required"}
: ${SPARK_MASTER_URL:?"SPARK_MASTER_URL is required"}
: ${OLLAMA_URL:?"OLLAMA_URL is required"}
: ${DUCKDB_PATH:="/app/data/crypto_analytics.db"}

# Créer les répertoires nécessaires
mkdir -p /app/data/analytics
mkdir -p /app/data/parquet
mkdir -p /app/logs
mkdir -p /app/cache

# Attente de Kafka
log "Waiting for Kafka to be ready..."
wait_for_kafka() {
    local retries=30
    local count=0
    
    while [ $count -lt $retries ]; do
        if python -c "
from kafka import KafkaConsumer
import sys
try:
    consumer = KafkaConsumer(
        bootstrap_servers='$KAFKA_BOOTSTRAP_SERVERS',
        request_timeout_ms=5000,
        api_version_auto_timeout_ms=5000
    )
    consumer.close()
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

# Attente de Spark Master
log "Waiting for Spark Master to be ready..."
wait_for_spark() {
    local retries=20
    local count=0
    
    while [ $count -lt $retries ]; do
        if curl -s --max-time 5 "http://spark-master:8080" | grep -q "Spark Master" 2>/dev/null; then
            log "Spark Master is ready!"
            return 0
        fi
        
        count=$((count + 1))
        log "Spark Master not ready yet (attempt $count/$retries), waiting 15s..."
        sleep 15
    done
    
    log "ERROR: Spark Master failed to become ready within timeout"
    return 1
}

wait_for_spark || exit 1

# Attente d'Ollama
log "Waiting for Ollama to be ready..."
wait_for_ollama() {
    local retries=30
    local count=0
    
    while [ $count -lt $retries ]; do
        if curl -s --max-time 10 "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
            log "Ollama is ready!"
            return 0
        fi
        
        count=$((count + 1))
        log "Ollama not ready yet (attempt $count/$retries), waiting 15s..."
        sleep 15
    done
    
    log "ERROR: Ollama failed to become ready within timeout"
    return 1
}

wait_for_ollama || exit 1

# Attente de PostgreSQL
log "Waiting for PostgreSQL to be ready..."
wait_for_postgres() {
    local retries=30
    local count=0

    while [ $count -lt $retries ]; do
        if python -c "
import psycopg2
import os
import sys
try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'postgres'),
        port=int(os.getenv('POSTGRES_PORT', '5432')),
        user=os.getenv('POSTGRES_USER', 'crypto_viz'),
        password=os.getenv('POSTGRES_PASSWORD', 'crypto_viz_password'),
        database=os.getenv('POSTGRES_DB', 'crypto_analytics'),
        connect_timeout=5
    )
    conn.close()
    sys.exit(0)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; then
            log "PostgreSQL is ready!"
            return 0
        fi

        count=$((count + 1))
        log "PostgreSQL not ready yet (attempt $count/$retries), waiting 5s..."
        sleep 5
    done

    log "ERROR: PostgreSQL failed to become ready within timeout"
    return 1
}

wait_for_postgres || exit 1

# Run database migrations
log "Running database migrations..."
python /app/migrate_db.py || {
    log "ERROR: Database migration failed"
    exit 1
}
log "Database migrations completed successfully!"

# Vérification du modèle Ollama
log "Checking Ollama model availability..."
python - <<EOF
import requests
import sys
import json

try:
    response = requests.get('$OLLAMA_URL/api/tags', timeout=10)
    if response.status_code == 200:
        models = response.json()
        model_names = [model['name'] for model in models.get('models', [])]
        
        if 'gemma3:4b' in model_names:
            print("✓ gemma3:4b model is available")
            sys.exit(0)
        else:
            print("⚠ gemma3:4b model not found, available models:")
            for name in model_names:
                print(f"  - {name}")
            print("Analytics will work with degraded sentiment analysis")
            sys.exit(0)
    else:
        print(f"Error checking models: HTTP {response.status_code}")
        sys.exit(1)
        
except Exception as e:
    print(f"Error connecting to Ollama: {e}")
    sys.exit(1)
EOF

# Initialisation DuckDB
log "Initializing DuckDB database..."
python - <<EOF
import duckdb
import os
import sys

try:
    # Créer le répertoire si nécessaire
    db_dir = os.path.dirname('$DUCKDB_PATH')
    os.makedirs(db_dir, exist_ok=True)
    
    # Connexion et création des tables de base
    conn = duckdb.connect('$DUCKDB_PATH')
    
    # Tables pour analytics
    conn.execute("""
        CREATE TABLE IF NOT EXISTS crypto_metrics (
            id INTEGER PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL,
            price DECIMAL(20,8),
            volume DECIMAL(20,8),
            market_cap DECIMAL(20,2),
            sentiment_score DECIMAL(3,2),
            ma_20 DECIMAL(20,8),
            ma_50 DECIMAL(20,8),
            rsi DECIMAL(5,2),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    
    # Index pour performance
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_crypto_symbol_timestamp 
        ON crypto_metrics(symbol, timestamp)
    """)
    
    # Table pour cache sentiment Ollama
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ollama_sentiment_cache (
            text_hash VARCHAR(32) PRIMARY KEY,
            sentiment VARCHAR(10) NOT NULL,
            confidence DECIMAL(3,2) NOT NULL,
            keywords TEXT,
            model_version VARCHAR(20),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    
    conn.close()
    print("DuckDB database initialized successfully!")
    
except Exception as e:
    print(f"Error initializing DuckDB: {e}")
    sys.exit(1)
EOF

# Démarrage du serveur de health check en arrière-plan
log "Starting health check server..."
python - <<EOF &
import uvicorn
from fastapi import FastAPI
import os
import duckdb
import requests

app = FastAPI()

@app.get("/health")
async def health_check():
    status = "healthy"
    services = {}
    
    # Check DuckDB
    try:
        conn = duckdb.connect('$DUCKDB_PATH')
        conn.execute("SELECT 1")
        conn.close()
        services["duckdb"] = "healthy"
    except Exception as e:
        services["duckdb"] = f"error: {str(e)}"
        status = "degraded"
    
    # Check Ollama
    try:
        response = requests.get('$OLLAMA_URL/api/tags', timeout=5)
        services["ollama"] = "healthy" if response.status_code == 200 else "error"
    except Exception as e:
        services["ollama"] = f"error: {str(e)}"
        status = "degraded"
    
    return {
        "status": status,
        "service": "crypto-viz-analytics",
        "version": "1.0",
        "services": services
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="error")
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

log "Pre-flight checks completed!"
log "Starting analytics processor..."

# Execute the CMD (Python script)
exec "$@"