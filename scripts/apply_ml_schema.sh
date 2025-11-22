#!/usr/bin/env bash
#
# Apply ML Analytics Schema to PostgreSQL
# This script applies the ML schema to an existing database
#

set -e

echo "=================================================="
echo "  Applying ML Analytics Schema"
echo "=================================================="

# Wait for postgres to be ready
echo "[1/3] Waiting for PostgreSQL to be ready..."
until docker exec crypto-viz-postgres pg_isready -U crypto_viz > /dev/null 2>&1; do
    echo "  Waiting for PostgreSQL..."
    sleep 2
done
echo "✓ PostgreSQL is ready"

# Check if ML tables already exist
echo "[2/3] Checking existing ML tables..."
EXISTING_TABLES=$(docker exec crypto-viz-postgres psql -U crypto_viz -d crypto_analytics -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'ml_%' OR table_name = 'anomalies' OR table_name = 'crypto_correlations' OR table_name = 'momentum_scores' OR table_name = 'portfolio_recommendations'")

if [ "$EXISTING_TABLES" -gt "5" ]; then
    echo "✓ ML tables already exist ($EXISTING_TABLES tables found)"
    echo "[3/3] Checking ML views..."

    # Check views
    EXISTING_VIEWS=$(docker exec crypto-viz-postgres psql -U crypto_viz -d crypto_analytics -t -c "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public' AND (table_name LIKE 'v_active_%' OR table_name LIKE 'v_latest_%' OR table_name LIKE 'v_current_%' OR table_name = 'v_correlation_matrix')")

    if [ "$EXISTING_VIEWS" -gt "5" ]; then
        echo "✓ ML views already exist ($EXISTING_VIEWS views found)"
        echo ""
        echo "=================================================="
        echo "  ML Schema Already Applied ✓"
        echo "=================================================="
        exit 0
    else
        echo "⚠ ML views missing ($EXISTING_VIEWS/8 found)"
        echo "[3/3] Applying ML schema..."
    fi
else
    echo "⚠ ML tables missing ($EXISTING_TABLES/9 found)"
    echo "[3/3] Applying ML schema..."
fi

# Apply the schema
echo "  Executing 02_ml_analytics_schema.sql..."
if docker exec -i crypto-viz-postgres psql -U crypto_viz -d crypto_analytics < database/init/02_ml_analytics_schema.sql > /tmp/ml_schema_apply.log 2>&1; then
    echo "✓ ML schema applied successfully"

    # Verify tables
    TABLES_AFTER=$(docker exec crypto-viz-postgres psql -U crypto_viz -d crypto_analytics -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND (table_name LIKE 'ml_%' OR table_name IN ('anomalies', 'crypto_correlations', 'momentum_scores', 'portfolio_recommendations'))")

    # Verify views
    VIEWS_AFTER=$(docker exec crypto-viz-postgres psql -U crypto_viz -d crypto_analytics -t -c "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public' AND (table_name LIKE 'v_active_%' OR table_name LIKE 'v_latest_%' OR table_name LIKE 'v_current_%' OR table_name = 'v_correlation_matrix')")

    echo ""
    echo "=================================================="
    echo "  ML Schema Applied Successfully ✓"
    echo "=================================================="
    echo "Tables created: $TABLES_AFTER"
    echo "Views created: $VIEWS_AFTER"
    echo ""
    echo "You can now test the ML endpoints:"
    echo "  curl http://localhost:8000/api/analytics/ml/clusters/statistics"
    echo "  curl http://localhost:8000/api/analytics/ml/predictions"
    echo "  curl http://localhost:8000/api/analytics/ml/correlations/matrix"
    echo "  curl http://localhost:8000/api/analytics/ml/anomalies"
    echo ""
else
    echo "✗ Error applying ML schema"
    echo "Check logs at /tmp/ml_schema_apply.log"
    cat /tmp/ml_schema_apply.log
    exit 1
fi
