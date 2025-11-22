#!/usr/bin/env python3
"""
PostgreSQL Data Writer
Handles writing analytics data to PostgreSQL
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
from psycopg2.pool import ThreadedConnectionPool
import json
import pandas as pd
import numpy as np
import time

logger = logging.getLogger(__name__)


def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    if isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if pd.isna(obj):
        return None
    raise TypeError(f"Type {type(obj)} not serializable")


class PostgreSQLWriter:
    """Handles writing data to PostgreSQL"""

    def __init__(self, min_conn: int = 1, max_conn: int = 10, max_retries: int = 10):
        """Initialize PostgreSQL connection pool with retry logic"""
        self.host = os.getenv('POSTGRES_HOST', 'postgres')
        self.port = int(os.getenv('POSTGRES_PORT', '5432'))
        self.user = os.getenv('POSTGRES_USER', 'crypto_viz')
        self.password = os.getenv('POSTGRES_PASSWORD', 'crypto_viz_password')
        self.database = os.getenv('POSTGRES_DB', 'crypto_analytics')

        # Retry connection with exponential backoff
        retry_delay = 2  # Initial delay in seconds
        last_exception = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Attempting to connect to PostgreSQL (attempt {attempt}/{max_retries})...")
                self.pool = ThreadedConnectionPool(
                    min_conn,
                    max_conn,
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database
                )
                logger.info(f"✓ PostgreSQL connection pool created ({min_conn}-{max_conn} connections)")
                return  # Success - exit constructor
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(f"Failed to connect to PostgreSQL (attempt {attempt}/{max_retries}): {e}")
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 30)  # Exponential backoff, max 30s
                else:
                    logger.error(f"Failed to create connection pool after {max_retries} attempts: {e}")
                    raise last_exception

    def get_connection(self):
        """Get a connection from the pool"""
        return self.pool.getconn()

    def return_connection(self, conn):
        """Return a connection to the pool"""
        self.pool.putconn(conn)

    def close_all(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("All PostgreSQL connections closed")

    def write_crypto_price(self, price_data: Dict[str, Any]) -> bool:
        """Write cryptocurrency price data"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO crypto_prices (
                    symbol, name, price, market_cap, volume_24h,
                    percent_change_1h, percent_change_24h, percent_change_7d,
                    circulating_supply, total_supply, max_supply, rank, timestamp
                ) VALUES (
                    %(symbol)s, %(name)s, %(price)s, %(market_cap)s, %(volume_24h)s,
                    %(percent_change_1h)s, %(percent_change_24h)s, %(percent_change_7d)s,
                    %(circulating_supply)s, %(total_supply)s, %(max_supply)s, %(rank)s, %(timestamp)s
                )
                ON CONFLICT (symbol, timestamp) DO UPDATE SET
                    price = EXCLUDED.price,
                    market_cap = EXCLUDED.market_cap,
                    volume_24h = EXCLUDED.volume_24h,
                    percent_change_1h = EXCLUDED.percent_change_1h,
                    percent_change_24h = EXCLUDED.percent_change_24h,
                    percent_change_7d = EXCLUDED.percent_change_7d
            """, price_data)

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error writing crypto price: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.return_connection(conn)

    def write_crypto_prices_batch(self, prices: List[Dict[str, Any]]) -> int:
        """Write multiple cryptocurrency prices in batch"""
        if not prices:
            return 0

        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            values = [
                (
                    p.get('symbol'),
                    p.get('name'),
                    p.get('price'),
                    p.get('market_cap'),
                    p.get('volume_24h'),
                    p.get('percent_change_1h'),
                    p.get('percent_change_24h'),
                    p.get('percent_change_7d'),
                    p.get('circulating_supply'),
                    p.get('total_supply'),
                    p.get('max_supply'),
                    p.get('rank'),
                    p.get('timestamp', datetime.now())
                )
                for p in prices
            ]

            execute_values(
                cursor,
                """
                INSERT INTO crypto_prices (
                    symbol, name, price, market_cap, volume_24h,
                    percent_change_1h, percent_change_24h, percent_change_7d,
                    circulating_supply, total_supply, max_supply, rank, timestamp
                ) VALUES %s
                ON CONFLICT (symbol, timestamp) DO NOTHING
                """,
                values
            )

            conn.commit()
            logger.info(f"Wrote {len(prices)} crypto prices to PostgreSQL")
            return len(prices)

        except Exception as e:
            logger.error(f"Error writing crypto prices batch: {e}")
            if conn:
                conn.rollback()
            return 0
        finally:
            if conn:
                self.return_connection(conn)

    def write_crypto_news(self, news_data: Dict[str, Any]) -> bool:
        """Write cryptocurrency news article"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO crypto_news (
                    source, author, title, description, url, url_to_image,
                    content, published_at, sentiment_score, sentiment_label,
                    keywords, mentioned_coins, analysis_method, confidence_score
                ) VALUES (
                    %(source)s, %(author)s, %(title)s, %(description)s, %(url)s,
                    %(url_to_image)s, %(content)s, %(published_at)s,
                    %(sentiment_score)s, %(sentiment_label)s,
                    %(keywords)s, %(mentioned_coins)s, %(analysis_method)s, %(confidence_score)s
                )
                ON CONFLICT (url) DO UPDATE SET
                    sentiment_score = EXCLUDED.sentiment_score,
                    sentiment_label = EXCLUDED.sentiment_label,
                    keywords = EXCLUDED.keywords,
                    analysis_method = EXCLUDED.analysis_method,
                    confidence_score = EXCLUDED.confidence_score
            """, news_data)

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error writing crypto news: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.return_connection(conn)

    def write_social_post(self, post_data: Dict[str, Any]) -> bool:
        """Write social media post"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO social_posts (
                    platform, post_id, subreddit, author, title, content,
                    url, score, num_comments, upvote_ratio,
                    sentiment_score, sentiment_label, mentioned_coins, published_at
                ) VALUES (
                    %(platform)s, %(post_id)s, %(subreddit)s, %(author)s,
                    %(title)s, %(content)s, %(url)s, %(score)s,
                    %(num_comments)s, %(upvote_ratio)s, %(sentiment_score)s,
                    %(sentiment_label)s, %(mentioned_coins)s, %(published_at)s
                )
                ON CONFLICT (platform, post_id) DO UPDATE SET
                    sentiment_score = EXCLUDED.sentiment_score,
                    sentiment_label = EXCLUDED.sentiment_label,
                    mentioned_coins = EXCLUDED.mentioned_coins
            """, post_data)

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error writing social post: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.return_connection(conn)

    def write_analytics_result(self, symbol: str, metric_type: str,
                               metric_value: float, metadata: Optional[Dict] = None) -> bool:
        """Write analytics result"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO analytics_results (
                    symbol, metric_type, metric_value, metadata
                ) VALUES (%s, %s, %s, %s)
            """, (symbol, metric_type, metric_value, json.dumps(metadata, default=json_serializer) if metadata else None))

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error writing analytics result: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.return_connection(conn)

    def write_sentiment_result(self, sentiment_data: Dict[str, Any]) -> bool:
        """Write sentiment analysis result"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO sentiment_results (
                    symbol, source, sentiment_score, sentiment_label,
                    sentiment_count, positive_count, negative_count,
                    neutral_count, time_window
                ) VALUES (
                    %(symbol)s, %(source)s, %(sentiment_score)s, %(sentiment_label)s,
                    %(sentiment_count)s, %(positive_count)s, %(negative_count)s,
                    %(neutral_count)s, %(time_window)s
                )
            """, sentiment_data)

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error writing sentiment result: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.return_connection(conn)

    def write_ml_prediction(self, prediction_data: Dict[str, Any]) -> bool:
        """Write ML model prediction"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO ml_predictions (
                    symbol, prediction_type, predicted_value, confidence,
                    predicted_at, valid_until, model_name, model_version,
                    rmse, r2_score, features_used, metadata
                ) VALUES (
                    %(symbol)s, %(prediction_type)s, %(predicted_value)s, %(confidence)s,
                    %(predicted_at)s, %(valid_until)s, %(model_name)s, %(model_version)s,
                    %(rmse)s, %(r2_score)s, %(features_used)s, %(metadata)s
                )
            """, {
                'symbol': prediction_data.get('symbol'),
                'prediction_type': prediction_data.get('prediction_type'),
                'predicted_value': prediction_data.get('predicted_value'),
                'confidence': prediction_data.get('confidence', 0.0),
                'predicted_at': prediction_data.get('predicted_at', datetime.now()),
                'valid_until': prediction_data.get('valid_until'),
                'model_name': prediction_data.get('model_name', 'LinearRegression'),
                'model_version': prediction_data.get('model_version', '1.0.0'),
                'rmse': prediction_data.get('rmse'),
                'r2_score': prediction_data.get('r2_score'),
                'features_used': json.dumps(prediction_data.get('features_used'), default=json_serializer) if prediction_data.get('features_used') else None,
                'metadata': json.dumps(prediction_data.get('metadata'), default=json_serializer) if prediction_data.get('metadata') else None
            })

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error writing ML prediction: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.return_connection(conn)

    def write_anomaly(self, anomaly_data: Dict[str, Any]) -> bool:
        """Write detected anomaly"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO anomalies (
                    symbol, anomaly_type, severity, anomaly_score, description,
                    expected_value, actual_value, deviation, detection_method,
                    detected_at, metadata
                ) VALUES (
                    %(symbol)s, %(anomaly_type)s, %(severity)s, %(anomaly_score)s,
                    %(description)s, %(expected_value)s, %(actual_value)s,
                    %(deviation)s, %(detection_method)s, %(detected_at)s, %(metadata)s
                )
            """, {
                'symbol': anomaly_data.get('symbol'),
                'anomaly_type': anomaly_data.get('anomaly_type'),
                'severity': anomaly_data.get('severity'),
                'anomaly_score': anomaly_data.get('anomaly_score'),
                'description': anomaly_data.get('description'),
                'expected_value': anomaly_data.get('expected_value'),
                'actual_value': anomaly_data.get('actual_value'),
                'deviation': anomaly_data.get('deviation'),
                'detection_method': anomaly_data.get('detection_method', 'z-score'),
                'detected_at': anomaly_data.get('detected_at', datetime.now()),
                'metadata': json.dumps(anomaly_data.get('metadata'), default=json_serializer) if anomaly_data.get('metadata') else None
            })

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error writing anomaly: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.return_connection(conn)

    def write_system_log(self, service: str, level: str, message: str,
                        metadata: Optional[Dict] = None) -> bool:
        """Write system log"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO system_logs (service, level, message, metadata)
                VALUES (%s, %s, %s, %s)
            """, (service, level, message, json.dumps(metadata, default=json_serializer) if metadata else None))

            conn.commit()
            return True

        except Exception as e:
            # Don't log error in write_system_log to avoid recursion
            return False
        finally:
            if conn:
                self.return_connection(conn)

    def write_cluster_assignment(self, cluster_data: Dict[str, Any]) -> bool:
        """Write ML cluster assignment"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO ml_cluster_assignments (
                    symbol, cluster_id, cluster_label, distance_to_centroid,
                    silhouette_score, features_used, feature_values,
                    model_version, num_clusters, assigned_at, metadata
                ) VALUES (
                    %(symbol)s, %(cluster_id)s, %(cluster_label)s, %(distance_to_centroid)s,
                    %(silhouette_score)s, %(features_used)s, %(feature_values)s,
                    %(model_version)s, %(num_clusters)s, %(assigned_at)s, %(metadata)s
                )
            """, {
                'symbol': cluster_data.get('symbol'),
                'cluster_id': cluster_data.get('cluster_id'),
                'cluster_label': cluster_data.get('cluster_label'),
                'distance_to_centroid': cluster_data.get('distance_to_centroid'),
                'silhouette_score': cluster_data.get('silhouette_score'),
                'features_used': json.dumps(cluster_data.get('features_used'), default=json_serializer) if cluster_data.get('features_used') else None,
                'feature_values': json.dumps(cluster_data.get('feature_values'), default=json_serializer) if cluster_data.get('feature_values') else None,
                'model_version': cluster_data.get('model_version', '1.0.0'),
                'num_clusters': cluster_data.get('num_clusters', 5),
                'assigned_at': cluster_data.get('assigned_at', datetime.now()),
                'metadata': json.dumps(cluster_data.get('metadata'), default=json_serializer) if cluster_data.get('metadata') else None
            })

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error writing cluster assignment: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.return_connection(conn)

    def write_cluster_assignments_batch(self, assignments: List[Dict[str, Any]]) -> int:
        """Write multiple cluster assignments in batch"""
        if not assignments:
            return 0

        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            values = [
                (
                    a.get('symbol'),
                    a.get('cluster_id'),
                    a.get('cluster_label'),
                    a.get('distance_to_centroid'),
                    a.get('silhouette_score'),
                    json.dumps(a.get('features_used'), default=json_serializer) if a.get('features_used') else None,
                    json.dumps(a.get('feature_values'), default=json_serializer) if a.get('feature_values') else None,
                    a.get('model_version', '1.0.0'),
                    a.get('num_clusters', 5),
                    a.get('assigned_at', datetime.now()),
                    json.dumps(a.get('metadata'), default=json_serializer) if a.get('metadata') else None
                )
                for a in assignments
            ]

            execute_values(
                cursor,
                """
                INSERT INTO ml_cluster_assignments (
                    symbol, cluster_id, cluster_label, distance_to_centroid,
                    silhouette_score, features_used, feature_values,
                    model_version, num_clusters, assigned_at, metadata
                ) VALUES %s
                """,
                values
            )

            conn.commit()
            logger.info(f"Wrote {len(assignments)} cluster assignments to PostgreSQL")
            return len(assignments)

        except Exception as e:
            logger.error(f"Error writing cluster assignments batch: {e}")
            if conn:
                conn.rollback()
            return 0
        finally:
            if conn:
                self.return_connection(conn)

    def write_correlation(self, correlation_data: Dict[str, Any]) -> bool:
        """Write crypto correlation data"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO crypto_correlations (
                    symbol_1, symbol_2, correlation_coefficient, correlation_type,
                    time_window, sample_size, p_value, is_significant, calculated_at
                ) VALUES (
                    %(symbol_1)s, %(symbol_2)s, %(correlation_coefficient)s, %(correlation_type)s,
                    %(time_window)s, %(sample_size)s, %(p_value)s, %(is_significant)s, %(calculated_at)s
                )
                ON CONFLICT (symbol_1, symbol_2, time_window, calculated_at) DO NOTHING
            """, {
                'symbol_1': correlation_data.get('symbol_1'),
                'symbol_2': correlation_data.get('symbol_2'),
                'correlation_coefficient': correlation_data.get('correlation_coefficient'),
                'correlation_type': correlation_data.get('correlation_type', 'pearson'),
                'time_window': correlation_data.get('time_window', '7d'),
                'sample_size': correlation_data.get('sample_size'),
                'p_value': correlation_data.get('p_value'),
                'is_significant': correlation_data.get('is_significant', False),
                'calculated_at': correlation_data.get('calculated_at', datetime.now())
            })

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error writing correlation: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.return_connection(conn)

    def write_correlations_batch(self, correlations: List[Dict[str, Any]]) -> int:
        """Write multiple correlations in batch"""
        if not correlations:
            return 0

        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            values = [
                (
                    c.get('symbol_1'),
                    c.get('symbol_2'),
                    c.get('correlation_coefficient'),
                    c.get('correlation_type', 'pearson'),
                    c.get('time_window', '7d'),
                    c.get('sample_size'),
                    c.get('p_value'),
                    c.get('is_significant', False),
                    c.get('calculated_at', datetime.now())
                )
                for c in correlations
            ]

            execute_values(
                cursor,
                """
                INSERT INTO crypto_correlations (
                    symbol_1, symbol_2, correlation_coefficient, correlation_type,
                    time_window, sample_size, p_value, is_significant, calculated_at
                ) VALUES %s
                ON CONFLICT (symbol_1, symbol_2, time_window, calculated_at) DO NOTHING
                """,
                values
            )

            conn.commit()
            logger.info(f"Wrote {len(correlations)} correlations to PostgreSQL")
            return len(correlations)

        except Exception as e:
            logger.error(f"Error writing correlations batch: {e}")
            if conn:
                conn.rollback()
            return 0
        finally:
            if conn:
                self.return_connection(conn)

    def write_momentum_score(self, momentum_data: Dict[str, Any]) -> bool:
        """Write momentum score"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO momentum_scores (
                    symbol, rsi_score, macd_score, volume_score, trend_score,
                    total_momentum_score, momentum_label, recommendation,
                    confidence, calculated_at, metadata
                ) VALUES (
                    %(symbol)s, %(rsi_score)s, %(macd_score)s, %(volume_score)s,
                    %(trend_score)s, %(total_momentum_score)s, %(momentum_label)s,
                    %(recommendation)s, %(confidence)s, %(calculated_at)s, %(metadata)s
                )
            """, {
                'symbol': momentum_data.get('symbol'),
                'rsi_score': momentum_data.get('rsi_score'),
                'macd_score': momentum_data.get('macd_score'),
                'volume_score': momentum_data.get('volume_score'),
                'trend_score': momentum_data.get('trend_score'),
                'total_momentum_score': momentum_data.get('total_momentum_score'),
                'momentum_label': momentum_data.get('momentum_label'),
                'recommendation': momentum_data.get('recommendation'),
                'confidence': momentum_data.get('confidence'),
                'calculated_at': momentum_data.get('calculated_at', datetime.now()),
                'metadata': json.dumps(momentum_data.get('metadata'), default=json_serializer) if momentum_data.get('metadata') else None
            })

            conn.commit()
            return True

        except Exception as e:
            logger.error(f"Error writing momentum score: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.return_connection(conn)
