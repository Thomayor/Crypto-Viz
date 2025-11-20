#!/usr/bin/env python3
"""
CRYPTO VIZ - Analytics Processor
Bootstrap Stack Integration: pandas + DuckDB + Spark
Main analytics service with PostgreSQL storage
"""

import asyncio
import logging
import os
import threading
from datetime import datetime, timedelta
import signal
import sys
from pathlib import Path
from typing import Dict, Any
import time

# pandas for data manipulation
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import analytics modules
from kafka_consumer_postgres import CryptoKafkaConsumer
from postgres_writer import PostgreSQLWriter
from duckdb_engine import DuckDBEngine
from spark_ml_pipeline import SparkMLPipeline
from crypto_metrics import CryptoMetrics


class BootstrapPipeline:
    """Bootstrap Stack pipeline: pandas → Parquet → DuckDB + Spark"""

    def __init__(self, pg_writer: PostgreSQLWriter):
        self.pg_writer = pg_writer
        self.parquet_dir = Path("/app/data/parquet")
        self.parquet_dir.mkdir(parents=True, exist_ok=True)

        # Load config for ML processing check
        self.config = self._load_config()

        # Initialize Bootstrap components
        try:
            self.duckdb = DuckDBEngine()
            logger.info("✓ DuckDB engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize DuckDB: {e}")
            self.duckdb = None

        try:
            self.spark_ml = SparkMLPipeline()
            logger.info("✓ Spark ML pipeline ready (lazy session)")
        except Exception as e:
            logger.error(f"Failed to initialize Spark ML pipeline: {e}")
            self.spark_ml = None

        try:
            kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
            self.crypto_metrics = CryptoMetrics(kafka_bootstrap_servers=kafka_servers)
            logger.info("✓ Crypto metrics calculator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Crypto Metrics: {e}")
            self.crypto_metrics = None

    def _load_config(self) -> dict:
        """Load analytics config from YAML file"""
        import yaml
        config_path = Path("/app/config/analytics_config.yaml")
        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
        return {}

    def extract_data_with_pandas(self, table: str, hours: int = 24, chunk_size: int = 10000) -> pd.DataFrame:
        """
        Extract data from PostgreSQL using pandas with chunking
        BOOTSTRAP REQUIREMENT: pandas data manipulation
        """
        try:
            logger.info(f"Extracting {table} data with pandas (chunked: {chunk_size} rows)...")
            start_time = time.time()

            conn = self.pg_writer.get_connection()

            # Query with timestamp filter (different columns for different tables)
            cutoff = datetime.now() - timedelta(hours=hours)

            # crypto_prices uses 'timestamp', crypto_news uses 'published_at'
            if table == 'crypto_prices':
                timestamp_col = 'timestamp'
            elif table == 'crypto_news':
                timestamp_col = 'published_at'
            else:
                timestamp_col = 'timestamp'  # default

            query = f"""
                SELECT * FROM {table}
                WHERE {timestamp_col} >= %s
                ORDER BY {timestamp_col} DESC
            """

            # Read in chunks for memory efficiency (EPITECH requirement)
            chunks = []
            for chunk in pd.read_sql_query(query, conn, params=(cutoff,), chunksize=chunk_size):
                # Data cleaning with pandas
                if 'symbol' in chunk.columns:
                    # crypto_prices: drop null symbols
                    chunk = chunk.dropna(subset=['symbol'])
                    chunk = chunk.drop_duplicates()
                elif 'url' in chunk.columns:
                    # crypto_news: drop null URLs, dedupe by URL only (entities column is unhashable)
                    chunk = chunk.dropna(subset=['url'])
                    chunk = chunk.drop_duplicates(subset=['url'])
                else:
                    # other tables: basic cleaning
                    chunk = chunk.dropna()

                chunks.append(chunk)

            self.pg_writer.return_connection(conn)

            # Concatenate chunks
            if chunks:
                df = pd.concat(chunks, ignore_index=True)
                elapsed = time.time() - start_time
                logger.info(f"✓ Extracted {len(df)} rows with pandas ({elapsed:.2f}s)")
                return df
            else:
                logger.warning(f"No data extracted from {table}")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Failed to extract data with pandas: {e}")
            return pd.DataFrame()

    def export_to_parquet(self, df: pd.DataFrame, filename: str) -> str:
        """
        Export pandas DataFrame to Parquet
        BOOTSTRAP REQUIREMENT: Parquet interchange format
        """
        try:
            if df.empty:
                logger.warning(f"Empty DataFrame, skipping Parquet export")
                return ""

            start_time = time.time()
            parquet_path = str(self.parquet_dir / filename)

            # Convert timestamp columns to datetime if needed
            for col in df.columns:
                if 'timestamp' in col.lower() or 'at' in col.lower():
                    if df[col].dtype == 'object':
                        df[col] = pd.to_datetime(df[col], errors='coerce')

            # Export with pandas using PyArrow engine for performance
            df.to_parquet(parquet_path, engine='pyarrow', compression='snappy', index=False)

            elapsed = time.time() - start_time
            file_size = Path(parquet_path).stat().st_size / (1024 * 1024)
            logger.info(f"✓ Exported {len(df)} rows to {parquet_path} ({file_size:.2f}MB, {elapsed:.2f}s)")

            return parquet_path

        except Exception as e:
            logger.error(f"Failed to export Parquet: {e}")
            return ""

    def run_duckdb_analytics(self, parquet_path: str) -> Dict[str, pd.DataFrame]:
        """
        Run SQL analytics on Parquet data using DuckDB
        BOOTSTRAP REQUIREMENT: DuckDB fast analytics
        """
        if not self.duckdb:
            logger.warning("DuckDB not initialized, skipping analytics")
            return {}

        try:
            logger.info("Running DuckDB analytics on Parquet data...")
            start_time = time.time()
            results = {}

            # Load Parquet into DuckDB
            table_name = Path(parquet_path).stem
            if not self.duckdb.load_parquet(parquet_path, table_name):
                return results

            # Price statistics
            if 'prices' in table_name:
                price_stats = self.duckdb.calculate_price_stats(hours=24)
                if not price_stats.empty:
                    results['price_stats'] = price_stats
                    logger.info(f"  ✓ Price stats: {len(price_stats)} records")

                # Price correlations
                correlations = self.duckdb.calculate_price_correlations(hours=168)
                if not correlations.empty:
                    results['correlations'] = correlations
                    logger.info(f"  ✓ Correlations: {len(correlations)} pairs")

                # Volume analysis
                volume_trends = self.duckdb.analyze_volume_trends(hours=24)
                if not volume_trends.empty:
                    results['volume_trends'] = volume_trends
                    logger.info(f"  ✓ Volume trends: {len(volume_trends)} records")

            # Sentiment aggregation
            if 'news' in table_name:
                sentiment = self.duckdb.aggregate_sentiment(hours=24)
                if not sentiment.empty:
                    results['sentiment'] = sentiment
                    logger.info(f"  ✓ Sentiment: {len(sentiment)} records")

            elapsed = time.time() - start_time
            logger.info(f"✓ DuckDB analytics completed ({elapsed:.2f}s)")

            return results

        except Exception as e:
            logger.error(f"DuckDB analytics failed: {e}")
            return {}

    def run_spark_ml(self, parquet_path: str) -> Dict[str, Any]:
        """
        Run distributed ML using Spark
        BOOTSTRAP REQUIREMENT: Spark ML distributed processing
        """
        if not self.spark_ml:
            logger.warning("Spark ML not initialized, skipping")
            return {}

        try:
            logger.info("Running Spark ML pipeline...")
            start_time = time.time()
            results = {}

            # Load Parquet into Spark
            df = self.spark_ml.load_parquet(parquet_path)
            if df is None or df.count() == 0:
                logger.warning("No data loaded into Spark")
                return results

            # Price prediction (Linear Regression)
            model = self.spark_ml.train_price_prediction_model(df, symbol="BTC")
            if model:
                predictions = self.spark_ml.predict_prices(model, df, symbol="BTC")
                if predictions:
                    # Save predictions to Parquet
                    pred_path = str(self.parquet_dir / "ml_predictions_btc.parquet")
                    self.spark_ml.save_parquet(predictions, pred_path)
                    results['predictions_path'] = pred_path
                    logger.info(f"  ✓ Price predictions saved")

            # Clustering (K-Means)
            cluster_model, clustered = self.spark_ml.perform_clustering(df, n_clusters=5)
            if clustered:
                cluster_path = str(self.parquet_dir / "crypto_clusters.parquet")
                self.spark_ml.save_parquet(clustered, cluster_path)
                results['clusters_path'] = cluster_path
                logger.info(f"  ✓ Clustering completed")

            # Anomaly detection
            df_prepared = self.spark_ml.prepare_crypto_features(df)
            anomalies = self.spark_ml.detect_anomalies(df_prepared, contamination=0.1)
            if anomalies and anomalies.count() > 0:
                anomaly_path = str(self.parquet_dir / "price_anomalies.parquet")
                self.spark_ml.save_parquet(anomalies, anomaly_path)
                results['anomalies_path'] = anomaly_path
                logger.info(f"  ✓ Anomaly detection: {anomalies.count()} anomalies")

            elapsed = time.time() - start_time
            logger.info(f"✓ Spark ML pipeline completed ({elapsed:.2f}s)")

            return results

        except Exception as e:
            logger.error(f"Spark ML failed: {e}")
            return {}

    def run_crypto_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate advanced crypto metrics and publish to Kafka

        Calculates:
        - Moving Averages (MA20, MA50, MA200)
        - RSI (Relative Strength Index)
        - MACD (Moving Average Convergence Divergence)
        - Trend detection
        - Breakout detection
        - Crypto correlations
        """
        try:
            if not self.crypto_metrics:
                logger.warning("Crypto metrics calculator not initialized")
                return {}

            logger.info("Running crypto metrics calculation...")
            start_time = time.time()

            # Calculate all technical indicators
            metrics = self.crypto_metrics.calculate_all_metrics(df)

            # Publish to Kafka
            published_counts = self.crypto_metrics.publish_to_kafka(metrics)

            elapsed = time.time() - start_time

            results = {
                'metrics_calculated': len(metrics.get('metrics', pd.DataFrame())),
                'correlations_calculated': len(metrics.get('correlations', pd.DataFrame())),
                'published_counts': published_counts,
                'elapsed_time': elapsed
            }

            logger.info(f"✓ Crypto metrics completed ({elapsed:.2f}s)")
            logger.info(f"  - Metrics: {results['metrics_calculated']} records")
            logger.info(f"  - Correlations: {results['correlations_calculated']} pairs")
            for topic, count in published_counts.items():
                logger.info(f"  - Published {count} messages to {topic}")

            return results

        except Exception as e:
            logger.error(f"Crypto metrics failed: {e}")
            return {}

    def save_results_to_postgres(self, duckdb_results: Dict[str, pd.DataFrame], spark_results: Dict[str, Any]):
        """Save analytics results back to PostgreSQL"""
        try:
            logger.info("Saving results to PostgreSQL...")

            # Save DuckDB results
            for result_type, df in duckdb_results.items():
                if df.empty:
                    continue

                if result_type == 'price_stats':
                    for _, row in df.iterrows():
                        self.pg_writer.write_analytics_result(
                            symbol=row.get('symbol', 'UNKNOWN'),
                            metric_type='price_stats',
                            metric_value=float(row.get('avg_price', 0)),
                            metadata=row.to_dict()
                        )

                elif result_type == 'sentiment':
                    for _, row in df.iterrows():
                        sentiment_score = float(row.get('avg_sentiment', 0))
                        news_count = int(row.get('news_count', 0))

                        # Determine sentiment label based on score
                        if sentiment_score > 0.1:
                            sentiment_label = 'positive'
                        elif sentiment_score < -0.1:
                            sentiment_label = 'negative'
                        else:
                            sentiment_label = 'neutral'

                        self.pg_writer.write_sentiment_result({
                            'symbol': row.get('symbol', 'UNKNOWN'),
                            'source': 'crypto-news',
                            'sentiment_score': sentiment_score,
                            'sentiment_label': sentiment_label,
                            'sentiment_count': news_count,
                            'positive_count': int(news_count * 0.4) if sentiment_score > 0 else 0,
                            'negative_count': int(news_count * 0.4) if sentiment_score < 0 else 0,
                            'neutral_count': int(news_count * 0.2),
                            'time_window': '24h'
                        })

            # Log Spark results
            if spark_results:
                self.pg_writer.write_system_log(
                    service='analytics-processor',
                    level='INFO',
                    message='Spark ML pipeline completed',
                    metadata=spark_results
                )

            logger.info("✓ Results saved to PostgreSQL")

        except Exception as e:
            logger.error(f"Failed to save results: {e}")


class PerformanceMetrics:
    """Track performance metrics for the Bootstrap pipeline"""

    def __init__(self):
        self.metrics = {
            'pipeline_runs': 0,
            'pandas_time': [],
            'duckdb_time': [],
            'spark_time': [],
            'total_time': [],
            'records_processed': []
        }

    def record_timing(self, stage: str, duration: float):
        """Record timing for a pipeline stage"""
        key = f"{stage}_time"
        if key in self.metrics:
            self.metrics[key].append(duration)

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        summary = {'pipeline_runs': self.metrics['pipeline_runs']}

        for key, values in self.metrics.items():
            if isinstance(values, list) and values:
                summary[f"{key}_avg"] = np.mean(values)
                summary[f"{key}_max"] = np.max(values)
                summary[f"{key}_min"] = np.min(values)

        return summary


class AnalyticsService:
    """Main analytics service orchestrator with Bootstrap Stack"""

    def __init__(self):
        self.running = True
        self.kafka_consumer = None
        self.kafka_thread = None
        self.pg_writer = None
        self.bootstrap_pipeline = None
        self.metrics = PerformanceMetrics()

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        if self.kafka_consumer:
            self.kafka_consumer.close()
        if self.bootstrap_pipeline and self.bootstrap_pipeline.spark_ml:
            self.bootstrap_pipeline.spark_ml.stop()
        sys.exit(0)

    def start_kafka_consumer(self):
        """Start Kafka consumer in background thread"""
        try:
            logger.info("Starting Kafka consumer thread...")
            self.kafka_consumer = CryptoKafkaConsumer()

            self.kafka_thread = threading.Thread(
                target=self.kafka_consumer.consume,
                daemon=True,
                name="KafkaConsumerThread"
            )
            self.kafka_thread.start()

            logger.info("✓ Kafka consumer thread started")
            return True

        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            return False

    async def run_bootstrap_analytics(self):
        """
        Run complete Bootstrap Stack analytics pipeline
        pandas → Parquet → DuckDB + Spark → PostgreSQL
        """
        try:
            logger.info("=" * 60)
            logger.info("BOOTSTRAP STACK ANALYTICS PIPELINE")
            logger.info("=" * 60)

            pipeline_start = time.time()

            # 1. Extract data with pandas (chunking for memory efficiency)
            pandas_start = time.time()
            df_prices = self.bootstrap_pipeline.extract_data_with_pandas('crypto_prices', hours=24)
            df_news = self.bootstrap_pipeline.extract_data_with_pandas('crypto_news', hours=24)
            pandas_time = time.time() - pandas_start
            self.metrics.record_timing('pandas', pandas_time)

            if df_prices.empty and df_news.empty:
                logger.warning("No data available for analytics")
                return

            # 2. Export to Parquet (interchange format for Bootstrap tools)
            parquet_prices = self.bootstrap_pipeline.export_to_parquet(df_prices, 'crypto_prices.parquet')
            parquet_news = self.bootstrap_pipeline.export_to_parquet(df_news, 'crypto_news.parquet')

            # 3. DuckDB Analytics (fast SQL queries on Parquet)
            duckdb_start = time.time()
            duckdb_results = {}
            if parquet_prices:
                duckdb_results.update(self.bootstrap_pipeline.run_duckdb_analytics(parquet_prices))
            if parquet_news:
                duckdb_results.update(self.bootstrap_pipeline.run_duckdb_analytics(parquet_news))
            duckdb_time = time.time() - duckdb_start
            self.metrics.record_timing('duckdb', duckdb_time)

            # 4. Spark ML (distributed machine learning) - OPTIONAL
            # Spark ML - can be slow (10+ min) but generates ML predictions
            spark_start = time.time()
            spark_results = {}
            # Check if ml_processing is enabled in config
            ml_enabled = False
            if hasattr(self.bootstrap_pipeline, 'config') and self.bootstrap_pipeline.config:
                stages = self.bootstrap_pipeline.config.get('pipeline', {}).get('stages', [])
                for stage in stages:
                    if stage.get('name') == 'ml_processing' and stage.get('enabled'):
                        ml_enabled = True
                        logger.info("ML processing is ENABLED in config")
                        break

            if ml_enabled and parquet_prices:
                logger.info("Running Spark ML processing (this may take several minutes)...")
                spark_results = self.bootstrap_pipeline.run_spark_ml(parquet_prices)
            else:
                if not ml_enabled:
                    logger.info("ML processing is DISABLED in config")
                if not parquet_prices:
                    logger.info("No parquet prices data available for ML processing")
            spark_time = time.time() - spark_start
            self.metrics.record_timing('spark', spark_time)

            # 5. Advanced Crypto Metrics (technical indicators)
            metrics_start = time.time()
            crypto_metrics_results = {}
            if not df_prices.empty:
                crypto_metrics_results = self.bootstrap_pipeline.run_crypto_metrics(df_prices)
            metrics_time = time.time() - metrics_start
            self.metrics.record_timing('crypto_metrics', metrics_time)

            # 6. Save results to PostgreSQL
            self.bootstrap_pipeline.save_results_to_postgres(duckdb_results, spark_results)

            # Record metrics
            total_time = time.time() - pipeline_start
            self.metrics.record_timing('total', total_time)
            self.metrics.metrics['pipeline_runs'] += 1
            self.metrics.record_timing('records', len(df_prices) + len(df_news))

            logger.info("=" * 60)
            logger.info(f"✓ BOOTSTRAP PIPELINE COMPLETED ({total_time:.2f}s)")
            logger.info(f"  - pandas: {pandas_time:.2f}s")
            logger.info(f"  - DuckDB: {duckdb_time:.2f}s")
            spark_status = f"{spark_time:.2f}s" if spark_time > 0.1 else "SKIPPED (disabled)"
            logger.info(f"  - Spark ML: {spark_status}")
            logger.info(f"  - Crypto Metrics: {metrics_time:.2f}s")
            logger.info(f"  - Records: {len(df_prices) + len(df_news)}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Bootstrap analytics failed: {e}", exc_info=True)

    async def run_analytics_loop(self):
        """Main analytics processing loop"""
        logger.info("Starting analytics loop...")

        # Initialize PostgreSQL writer and Bootstrap pipeline
        self.pg_writer = PostgreSQLWriter(min_conn=1, max_conn=5)
        self.bootstrap_pipeline = BootstrapPipeline(self.pg_writer)

        batch_interval = int(os.getenv('ANALYTICS_INTERVAL', '300'))  # 5 minutes
        iteration = 0

        while self.running:
            try:
                iteration += 1
                start_time = datetime.now()

                logger.info(f"Analytics iteration #{iteration} - {start_time}")

                # Run Bootstrap Stack pipeline
                await self.run_bootstrap_analytics()

                # Log performance metrics
                metrics_summary = self.metrics.get_summary()
                self.pg_writer.write_system_log(
                    service='analytics-processor',
                    level='INFO',
                    message=f'Analytics iteration #{iteration} completed',
                    metadata=metrics_summary
                )

                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"Analytics iteration #{iteration} completed in {elapsed:.2f}s")

                # Sleep until next iteration
                await asyncio.sleep(batch_interval)

            except Exception as e:
                logger.error(f"Error in analytics loop: {e}", exc_info=True)
                await asyncio.sleep(30)

    async def run(self):
        """Main service orchestration"""
        logger.info("=" * 60)
        logger.info("CRYPTO VIZ ANALYTICS SERVICE")
        logger.info("=" * 60)
        logger.info("Bootstrap Stack: pandas + DuckDB + Spark ✓")
        logger.info("Storage: PostgreSQL + DuckDB ✓")
        logger.info("Data Pipeline: Kafka → Analytics → PostgreSQL ✓")
        logger.info("=" * 60)

        # Start Kafka consumer in background
        if not self.start_kafka_consumer():
            logger.error("Failed to start Kafka consumer, exiting")
            sys.exit(1)

        # Log startup to PostgreSQL
        try:
            pg_writer = PostgreSQLWriter(min_conn=1, max_conn=2)
            pg_writer.write_system_log(
                service='analytics-processor',
                level='INFO',
                message='Analytics service started successfully with Bootstrap Stack',
                metadata={
                    'timestamp': datetime.now().isoformat(),
                    'bootstrap_stack': ['pandas', 'duckdb', 'spark'],
                    'kafka_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
                    'postgres_host': os.getenv('POSTGRES_HOST'),
                    'spark_master': os.getenv('SPARK_MASTER_URL')
                }
            )
            pg_writer.close_all()
        except Exception as e:
            logger.warning(f"Could not log startup to PostgreSQL: {e}")

        # Run analytics loop
        try:
            await self.run_analytics_loop()
        except Exception as e:
            logger.error(f"Analytics loop failed: {e}")
            raise
        finally:
            # Cleanup
            if self.kafka_consumer:
                self.kafka_consumer.close()
            if self.pg_writer:
                self.pg_writer.close_all()
            if self.bootstrap_pipeline:
                if self.bootstrap_pipeline.duckdb:
                    self.bootstrap_pipeline.duckdb.close()
                if self.bootstrap_pipeline.spark_ml:
                    self.bootstrap_pipeline.spark_ml.stop()

            logger.info("Analytics service stopped")


async def main():
    """Main entry point"""
    service = AnalyticsService()
    await service.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        sys.exit(1)
