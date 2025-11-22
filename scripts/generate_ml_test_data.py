#!/usr/bin/env python3
"""
Generate test ML data for immediate frontend display
This bypasses the slow Spark ML pipeline and creates sample data directly in PostgreSQL
"""

import psycopg2
from datetime import datetime, timedelta, timezone
import uuid
import random

# Database connection
import os
conn_params = {
    'host': os.getenv('POSTGRES_HOST', 'postgres'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'user': os.getenv('POSTGRES_USER', 'crypto_viz'),
    'password': os.getenv('POSTGRES_PASSWORD', 'crypto_viz_password'),
    'database': os.getenv('POSTGRES_DB', 'crypto_analytics')
}

symbols = ['BTC', 'ETH', 'BNB', 'XRP', 'USDT', 'USDC']
prediction_types = ['price', 'volatility', 'trend', 'momentum']
anomaly_types = ['price_spike', 'price_drop', 'volume_spike', 'volatility', 'correlation_break']
severities = ['low', 'medium', 'high', 'critical']

try:
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()

    print("🔄 Generating ML test data...")

    # 1. Generate Price Predictions
    print("  📊 Creating price predictions...")
    for symbol in symbols:
        for pred_type in prediction_types:
            # Create 3 predictions per symbol-type combination
            for i in range(3):
                predicted_value = random.uniform(1000, 100000) if symbol == 'BTC' else random.uniform(100, 5000)
                confidence = random.uniform(0.7, 0.95)
                predicted_at = datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 12))
                valid_until = predicted_at + timedelta(hours=24)

                cur.execute("""
                    INSERT INTO ml_predictions
                    (id, symbol, prediction_type, predicted_value, confidence,
                     predicted_at, valid_until, model_name, model_version, rmse, r2_score)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    str(uuid.uuid4()), symbol, pred_type, predicted_value, confidence,
                    predicted_at, valid_until, 'LinearRegression', 'v1.0',
                    random.uniform(100, 1000), random.uniform(0.75, 0.95)
                ))

    conn.commit()
    print(f"  ✓ Created {len(symbols) * len(prediction_types) * 3} predictions")

    # 2. Generate Anomalies
    print("  🚨 Creating anomaly alerts...")
    for symbol in symbols[:3]:  # Only first 3 symbols
        for severity in severities[:2]:  # Only low and medium
            anomaly_type = random.choice(anomaly_types)
            anomaly_score = random.uniform(0.6, 0.9)
            detected_at = datetime.now(timezone.utc) - timedelta(hours=random.randint(0, 6))

            description = f"{anomaly_type.replace('_', ' ').title()} detected for {symbol}"

            cur.execute("""
                INSERT INTO anomalies
                (id, symbol, anomaly_type, severity, anomaly_score, description,
                 detection_method, is_resolved, detected_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()), symbol, anomaly_type, severity, anomaly_score,
                description, 'isolation_forest', False, detected_at
            ))

    conn.commit()
    print(f"  ✓ Created {len(symbols[:3]) * len(severities[:2])} anomalies")

    # 3. Generate Cluster Assignments
    print("  🎯 Creating cluster assignments...")
    for symbol in symbols:
        cluster_id = random.randint(0, 4)  # 5 clusters (0-4)
        distance_to_centroid = random.uniform(0.1, 2.5)
        assigned_at = datetime.now(timezone.utc)

        cur.execute("""
            INSERT INTO ml_cluster_assignments
            (id, symbol, cluster_id, distance_to_centroid, assigned_at, model_version)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            str(uuid.uuid4()), symbol, cluster_id, distance_to_centroid,
            assigned_at, 'v1.0'
        ))

    conn.commit()
    print(f"  ✓ Created {len(symbols)} cluster assignments")

    # 4. Register ML Models
    print("  📋 Registering ML models...")
    models = [
        ('LinearRegression', 'regression', 'v1.0', '{"rmse": 450.32, "mae": 320.18, "r2_score": 0.89}'),
        ('KMeans', 'clustering', 'v1.0', '{"n_clusters": 5, "inertia": 1234.56, "silhouette_score": 0.76}'),
        ('IsolationForest', 'anomaly_detection', 'v1.0', '{"contamination": 0.1, "n_estimators": 100, "accuracy": 0.82}')
    ]

    for model_name, model_type, model_version, metrics in models:
        trained_at = datetime.now(timezone.utc) - timedelta(hours=1)

        cur.execute("""
            INSERT INTO ml_model_registry
            (id, model_name, model_type, model_version, performance_metrics,
             trained_at, is_active, is_production)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s)
            ON CONFLICT (model_name, model_version) DO NOTHING
        """, (
            str(uuid.uuid4()), model_name, model_type, model_version, metrics,
            trained_at, True, True
        ))

    conn.commit()
    print(f"  ✓ Registered {len(models)} ML models")

    # 5. Generate Correlations
    print("  🔗 Creating price correlations...")
    correlation_count = 0
    for i, symbol1 in enumerate(symbols):
        for symbol2 in symbols[i+1:]:
            correlation_coefficient = random.uniform(-0.8, 0.9)
            correlation_type = random.choice(['pearson', 'spearman', 'kendall'])
            time_window = '7d'
            sample_size = random.randint(100, 500)
            is_significant = abs(correlation_coefficient) > 0.5
            calculated_at = datetime.now(timezone.utc)

            cur.execute("""
                INSERT INTO crypto_correlations
                (id, symbol_1, symbol_2, correlation_coefficient, correlation_type,
                 time_window, sample_size, is_significant, calculated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(uuid.uuid4()), symbol1, symbol2, correlation_coefficient,
                correlation_type, time_window, sample_size, is_significant, calculated_at
            ))
            correlation_count += 1

    conn.commit()
    print(f"  ✓ Created {correlation_count} correlations")

    print("\n✅ ML test data generated successfully!")
    print("\n📊 Summary:")
    cur.execute("SELECT COUNT(*) FROM ml_predictions")
    print(f"   • Predictions: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM anomalies")
    print(f"   • Anomalies: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM ml_cluster_assignments")
    print(f"   • Cluster Assignments: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM ml_model_registry")
    print(f"   • ML Models: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM crypto_correlations")
    print(f"   • Correlations: {cur.fetchone()[0]}")

    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    try:
        if conn:
            conn.rollback()
    except:
        pass
    raise
