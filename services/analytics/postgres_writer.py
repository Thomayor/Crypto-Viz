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

    def __init__(self, min_conn: int = 1, max_conn: int = 10):
        """Initialize PostgreSQL connection pool"""
        self.host = os.getenv('POSTGRES_HOST', 'postgres')
        self.port = int(os.getenv('POSTGRES_PORT', '5432'))
        self.user = os.getenv('POSTGRES_USER', 'crypto_viz')
        self.password = os.getenv('POSTGRES_PASSWORD', 'crypto_viz_password')
        self.database = os.getenv('POSTGRES_DB', 'crypto_analytics')

        try:
            self.pool = ThreadedConnectionPool(
                min_conn,
                max_conn,
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            logger.info(f"PostgreSQL connection pool created ({min_conn}-{max_conn} connections)")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

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
                    symbol, model_name, prediction_type, predicted_value,
                    confidence_score, features, prediction_horizon, valid_until
                ) VALUES (
                    %(symbol)s, %(model_name)s, %(prediction_type)s, %(predicted_value)s,
                    %(confidence_score)s, %(features)s, %(prediction_horizon)s, %(valid_until)s
                )
            """, prediction_data)

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
                    symbol, anomaly_type, severity, description,
                    anomaly_score, metadata
                ) VALUES (
                    %(symbol)s, %(anomaly_type)s, %(severity)s, %(description)s,
                    %(anomaly_score)s, %(metadata)s
                )
            """, anomaly_data)

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
