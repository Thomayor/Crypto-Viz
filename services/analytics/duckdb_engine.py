#!/usr/bin/env python3
"""
DuckDB Analytics Engine
Fast SQL analytics on Parquet files with efficient querying
Part of Bootstrap Stack (EPITECH requirement)
"""

import duckdb
import pandas as pd
import logging
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
import yaml
import time

logger = logging.getLogger(__name__)


class DuckDBEngine:
    """DuckDB engine for fast analytical queries on Parquet data"""

    def __init__(self, config_path: str = "config/analytics_config.yaml"):
        """Initialize DuckDB connection with configuration"""
        self.config = self._load_config(config_path)
        self.db_path = self.config['bootstrap_stack']['duckdb']['database_path']
        self.memory_limit = self.config['bootstrap_stack']['duckdb']['memory_limit']
        self.threads = self.config['bootstrap_stack']['duckdb']['threads']

        # Create data directory if needed
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize connection
        self.conn = self._create_connection()
        logger.info(f"DuckDB initialized: {self.db_path}")

    def _load_config(self, config_path: str) -> Dict:
        """Load analytics configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}: {e}")
            # Return minimal default config
            return {
                'bootstrap_stack': {
                    'duckdb': {
                        'database_path': '/app/data/crypto_analytics.db',
                        'memory_limit': '2GB',
                        'threads': 4,
                        'enable_optimization': True
                    }
                }
            }

    def _create_connection(self) -> duckdb.DuckDBPyConnection:
        """Create and configure DuckDB connection"""
        conn = duckdb.connect(self.db_path)

        # Configure DuckDB
        conn.execute(f"SET memory_limit='{self.memory_limit}'")
        conn.execute(f"SET threads={self.threads}")
        conn.execute("SET enable_object_cache=true")

        # Enable Parquet optimization
        conn.execute("SET preserve_insertion_order=false")

        logger.info(f"DuckDB connection configured (memory: {self.memory_limit}, threads: {self.threads})")
        return conn

    def close(self):
        """Close DuckDB connection"""
        if self.conn:
            self.conn.close()
            logger.info("DuckDB connection closed")

    # ========================================
    # DATA LOADING & PARQUET OPERATIONS
    # ========================================

    def load_parquet(self, parquet_path: str, table_name: str) -> bool:
        """Load Parquet file into DuckDB table"""
        try:
            start_time = time.time()

            # Create or replace table from Parquet
            self.conn.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT * FROM read_parquet('{parquet_path}')
            """)

            elapsed = time.time() - start_time
            count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

            logger.info(f"✓ Loaded {count} rows from Parquet into {table_name} ({elapsed:.2f}s)")
            return True

        except Exception as e:
            logger.error(f"Failed to load Parquet {parquet_path}: {e}")
            return False

    def load_parquet_directory(self, directory: str, table_name: str, pattern: str = "*.parquet") -> bool:
        """Load all Parquet files from directory"""
        try:
            start_time = time.time()

            # Load all matching Parquet files
            parquet_glob = f"{directory}/{pattern}"
            self.conn.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT * FROM read_parquet('{parquet_glob}', union_by_name=true)
            """)

            elapsed = time.time() - start_time
            count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

            logger.info(f"✓ Loaded {count} rows from {parquet_glob} into {table_name} ({elapsed:.2f}s)")
            return True

        except Exception as e:
            logger.error(f"Failed to load Parquet directory {directory}: {e}")
            return False

    def export_to_parquet(self, table_name: str, output_path: str, compression: str = 'snappy') -> bool:
        """Export DuckDB table to Parquet"""
        try:
            start_time = time.time()

            # Create output directory
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            # Export to Parquet
            self.conn.execute(f"""
                COPY {table_name}
                TO '{output_path}'
                (FORMAT PARQUET, COMPRESSION '{compression}')
            """)

            elapsed = time.time() - start_time
            logger.info(f"✓ Exported {table_name} to {output_path} ({elapsed:.2f}s)")
            return True

        except Exception as e:
            logger.error(f"Failed to export {table_name} to Parquet: {e}")
            return False

    # ========================================
    # ANALYTICS QUERIES
    # ========================================

    def query(self, sql: str) -> pd.DataFrame:
        """Execute SQL query and return pandas DataFrame"""
        try:
            start_time = time.time()
            result = self.conn.execute(sql).fetchdf()
            elapsed = time.time() - start_time

            logger.debug(f"Query executed in {elapsed:.2f}s, returned {len(result)} rows")
            return result

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return pd.DataFrame()

    def execute(self, sql: str) -> bool:
        """Execute SQL statement (no return)"""
        try:
            self.conn.execute(sql)
            return True
        except Exception as e:
            logger.error(f"Execute failed: {e}")
            return False

    # ========================================
    # PRICE ANALYTICS
    # ========================================

    def calculate_price_stats(self, hours: int = 24) -> pd.DataFrame:
        """Calculate price statistics (volatility, ranges, averages)"""
        try:
            sql = f"""
            SELECT
                symbol,
                date_trunc('hour', timestamp) as hour,
                COUNT(*) as sample_count,
                AVG(price) as avg_price,
                MIN(price) as min_price,
                MAX(price) as max_price,
                STDDEV(price) as volatility,
                MAX(price) - MIN(price) as price_range,
                (MAX(price) - MIN(price)) / AVG(price) * 100 as range_pct
            FROM crypto_prices
            WHERE timestamp >= NOW() - INTERVAL '{hours} hours'
            GROUP BY symbol, hour
            ORDER BY hour DESC, symbol
            """

            result = self.query(sql)
            logger.info(f"Calculated price stats for {len(result)} symbol-hour pairs")
            return result

        except Exception as e:
            logger.error(f"Failed to calculate price stats: {e}")
            return pd.DataFrame()

    def calculate_moving_averages(self, symbol: str, windows: List[int] = [15, 60, 240, 1440]) -> pd.DataFrame:
        """Calculate moving averages for different time windows (in minutes)"""
        try:
            # Build window clauses
            window_clauses = []
            for window in windows:
                window_clauses.append(f"""
                    AVG(price) OVER (
                        PARTITION BY symbol
                        ORDER BY timestamp
                        ROWS BETWEEN {window} PRECEDING AND CURRENT ROW
                    ) as ma_{window}m
                """)

            sql = f"""
            SELECT
                symbol,
                timestamp,
                price,
                {', '.join(window_clauses)}
            FROM crypto_prices
            WHERE symbol = '{symbol}'
            ORDER BY timestamp DESC
            LIMIT 1000
            """

            result = self.query(sql)
            logger.info(f"Calculated moving averages for {symbol}")
            return result

        except Exception as e:
            logger.error(f"Failed to calculate moving averages: {e}")
            return pd.DataFrame()

    def calculate_price_changes(self, hours: int = 24) -> pd.DataFrame:
        """Calculate price changes over various timeframes"""
        try:
            sql = f"""
            WITH price_data AS (
                SELECT
                    symbol,
                    timestamp,
                    price,
                    LAG(price, 60) OVER (PARTITION BY symbol ORDER BY timestamp) as price_1h_ago,
                    LAG(price, 240) OVER (PARTITION BY symbol ORDER BY timestamp) as price_4h_ago,
                    LAG(price, 1440) OVER (PARTITION BY symbol ORDER BY timestamp) as price_24h_ago
                FROM crypto_prices
                WHERE timestamp >= NOW() - INTERVAL '{hours + 24} hours'
            )
            SELECT
                symbol,
                timestamp,
                price,
                (price - price_1h_ago) / price_1h_ago * 100 as change_1h_pct,
                (price - price_4h_ago) / price_4h_ago * 100 as change_4h_pct,
                (price - price_24h_ago) / price_24h_ago * 100 as change_24h_pct
            FROM price_data
            WHERE timestamp >= NOW() - INTERVAL '{hours} hours'
                AND price_1h_ago IS NOT NULL
            ORDER BY timestamp DESC
            """

            result = self.query(sql)
            logger.info(f"Calculated price changes for {len(result)} records")
            return result

        except Exception as e:
            logger.error(f"Failed to calculate price changes: {e}")
            return pd.DataFrame()

    # ========================================
    # CORRELATION ANALYSIS
    # ========================================

    def calculate_price_correlations(self, hours: int = 168) -> pd.DataFrame:
        """Calculate price correlations between crypto pairs"""
        try:
            sql = f"""
            WITH aligned_prices AS (
                SELECT
                    date_trunc('minute', timestamp) as minute,
                    symbol,
                    AVG(price) as price
                FROM crypto_prices
                WHERE timestamp >= NOW() - INTERVAL '{hours} hours'
                GROUP BY minute, symbol
            )
            SELECT
                a.symbol as symbol_a,
                b.symbol as symbol_b,
                CORR(a.price, b.price) as correlation,
                COUNT(*) as sample_count
            FROM aligned_prices a
            JOIN aligned_prices b ON a.minute = b.minute
            WHERE a.symbol < b.symbol  -- Avoid duplicates
            GROUP BY a.symbol, b.symbol
            HAVING COUNT(*) >= 100  -- Minimum samples
                AND CORR(a.price, b.price) IS NOT NULL
            ORDER BY ABS(correlation) DESC
            """

            result = self.query(sql)
            logger.info(f"Calculated {len(result)} price correlations")
            return result

        except Exception as e:
            logger.error(f"Failed to calculate correlations: {e}")
            return pd.DataFrame()

    # ========================================
    # SENTIMENT ANALYTICS
    # ========================================

    def aggregate_sentiment(self, hours: int = 24) -> pd.DataFrame:
        """Aggregate sentiment scores by symbol and timeframe"""
        try:
            sql = f"""
            SELECT
                symbol,
                date_trunc('hour', published_at) as hour,
                AVG(sentiment_score) as avg_sentiment,
                STDDEV(sentiment_score) as sentiment_volatility,
                COUNT(*) as article_count,
                SUM(CASE WHEN sentiment_score > 0.5 THEN 1 ELSE 0 END) as positive_count,
                SUM(CASE WHEN sentiment_score < -0.5 THEN 1 ELSE 0 END) as negative_count
            FROM (
                SELECT
                    UNNEST(mentioned_coins) as symbol,
                    published_at,
                    sentiment_score
                FROM crypto_news
                WHERE published_at >= NOW() - INTERVAL '{hours} hours'
                    AND mentioned_coins IS NOT NULL
            )
            GROUP BY symbol, hour
            ORDER BY hour DESC, symbol
            """

            result = self.query(sql)
            logger.info(f"Aggregated sentiment for {len(result)} symbol-hour pairs")
            return result

        except Exception as e:
            logger.error(f"Failed to aggregate sentiment: {e}")
            return pd.DataFrame()

    # ========================================
    # VOLUME ANALYTICS
    # ========================================

    def analyze_volume_trends(self, hours: int = 24) -> pd.DataFrame:
        """Analyze trading volume trends"""
        try:
            sql = f"""
            SELECT
                symbol,
                date_trunc('hour', timestamp) as hour,
                AVG(volume_24h) as avg_volume,
                MAX(volume_24h) as max_volume,
                MIN(volume_24h) as min_volume,
                STDDEV(volume_24h) as volume_volatility,
                (MAX(volume_24h) - MIN(volume_24h)) / AVG(volume_24h) * 100 as volume_range_pct
            FROM crypto_prices
            WHERE timestamp >= NOW() - INTERVAL '{hours} hours'
                AND volume_24h IS NOT NULL
            GROUP BY symbol, hour
            ORDER BY hour DESC, avg_volume DESC
            """

            result = self.query(sql)
            logger.info(f"Analyzed volume trends for {len(result)} records")
            return result

        except Exception as e:
            logger.error(f"Failed to analyze volume: {e}")
            return pd.DataFrame()

    # ========================================
    # DATA QUALITY
    # ========================================

    def check_data_quality(self, table_name: str) -> Dict[str, Any]:
        """Check data quality metrics for a table"""
        try:
            metrics = {}

            # Row count
            count = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            metrics['row_count'] = count

            # Null counts per column
            columns = self.conn.execute(f"DESCRIBE {table_name}").fetchdf()['column_name'].tolist()
            null_counts = {}

            for col in columns:
                null_count = self.conn.execute(
                    f"SELECT COUNT(*) FROM {table_name} WHERE {col} IS NULL"
                ).fetchone()[0]
                null_counts[col] = null_count

            metrics['null_counts'] = null_counts
            metrics['null_percentage'] = {
                col: (null_count / count * 100) if count > 0 else 0
                for col, null_count in null_counts.items()
            }

            # Duplicate check
            if 'id' in columns:
                duplicates = self.conn.execute(
                    f"SELECT COUNT(*) - COUNT(DISTINCT id) FROM {table_name}"
                ).fetchone()[0]
                metrics['duplicate_ids'] = duplicates

            logger.info(f"Data quality check for {table_name}: {count} rows")
            return metrics

        except Exception as e:
            logger.error(f"Failed to check data quality: {e}")
            return {}

    # ========================================
    # PERFORMANCE METRICS
    # ========================================

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get DuckDB performance metrics"""
        try:
            metrics = {}

            # Database size
            if os.path.exists(self.db_path):
                metrics['database_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)

            # Table information
            tables = self.conn.execute("SHOW TABLES").fetchdf()
            metrics['table_count'] = len(tables)

            # Memory usage
            memory_info = self.conn.execute("SELECT * FROM duckdb_memory()").fetchdf()
            if not memory_info.empty:
                metrics['memory_usage_mb'] = memory_info['memory_usage_bytes'].sum() / (1024 * 1024)

            return metrics

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}


# Utility functions for common operations
def create_engine(config_path: str = "config/analytics_config.yaml") -> DuckDBEngine:
    """Factory function to create DuckDB engine"""
    return DuckDBEngine(config_path)
