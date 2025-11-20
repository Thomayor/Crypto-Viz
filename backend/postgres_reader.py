#!/usr/bin/env python3
"""
PostgreSQL Data Reader for Backend API
Handles reading analytics data from PostgreSQL
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
import json

logger = logging.getLogger(__name__)


class PostgreSQLReader:
    """Handles reading data from PostgreSQL"""

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
                database=self.database,
                cursor_factory=RealDictCursor
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

    def get_latest_crypto_prices(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get latest cryptocurrency prices"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM v_latest_crypto_prices
                ORDER BY rank ASC NULLS LAST, market_cap DESC NULLS LAST
                LIMIT %s
            """, (limit,))

            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error getting latest crypto prices: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)

    def get_crypto_price_history(self, symbol: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get price history for a cryptocurrency"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cutoff = datetime.now() - timedelta(hours=hours)
            cursor.execute("""
                SELECT id, symbol, name, price, market_cap, volume_24h,
                       percent_change_1h, percent_change_24h, percent_change_7d,
                       rank, timestamp
                FROM crypto_prices
                WHERE symbol = %s AND timestamp >= %s
                ORDER BY timestamp ASC
            """, (symbol.upper(), cutoff))

            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error getting price history for {symbol}: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)

    def get_latest_crypto_news(self, limit: int = 20, hours: int = 24) -> List[Dict[str, Any]]:
        """Get latest cryptocurrency news"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cutoff = datetime.now() - timedelta(hours=hours)
            cursor.execute("""
                SELECT id, source, author, title, description, url,
                       url_to_image, published_at, sentiment_score,
                       sentiment_label, analysis_method, confidence_score,
                       keywords, mentioned_coins
                FROM crypto_news
                WHERE published_at >= %s
                ORDER BY published_at DESC
                LIMIT %s
            """, (cutoff, limit))

            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error getting latest crypto news: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)

    def get_latest_social_posts(self, limit: int = 20, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get latest social media posts"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            if platform:
                cursor.execute("""
                    SELECT id, platform, post_id, subreddit, author, title,
                           content, url, score, num_comments, upvote_ratio,
                           sentiment_score, sentiment_label, mentioned_coins,
                           published_at
                    FROM social_posts
                    WHERE platform = %s
                    ORDER BY published_at DESC
                    LIMIT %s
                """, (platform, limit))
            else:
                cursor.execute("""
                    SELECT id, platform, post_id, subreddit, author, title,
                           content, url, score, num_comments, upvote_ratio,
                           sentiment_score, sentiment_label, mentioned_coins,
                           published_at
                    FROM social_posts
                    ORDER BY published_at DESC
                    LIMIT %s
                """, (limit,))

            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error getting social posts: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)

    def get_analytics_results(self, symbol: Optional[str] = None,
                             metric_type: Optional[str] = None,
                             hours: int = 24) -> List[Dict[str, Any]]:
        """Get analytics results"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cutoff = datetime.now() - timedelta(hours=hours)

            if symbol and metric_type:
                cursor.execute("""
                    SELECT * FROM analytics_results
                    WHERE symbol = %s AND metric_type = %s AND calculated_at >= %s
                    ORDER BY calculated_at DESC
                """, (symbol.upper(), metric_type, cutoff))
            elif symbol:
                cursor.execute("""
                    SELECT * FROM analytics_results
                    WHERE symbol = %s AND calculated_at >= %s
                    ORDER BY calculated_at DESC
                """, (symbol.upper(), cutoff))
            else:
                cursor.execute("""
                    SELECT * FROM analytics_results
                    WHERE calculated_at >= %s
                    ORDER BY calculated_at DESC
                    LIMIT 100
                """, (cutoff,))

            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error getting analytics results: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)

    def get_sentiment_summary(self, symbol: Optional[str] = None,
                             time_window: str = '24h') -> List[Dict[str, Any]]:
        """Get sentiment analysis summary"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            if symbol:
                cursor.execute("""
                    SELECT * FROM sentiment_results
                    WHERE symbol = %s AND time_window = %s
                    ORDER BY calculated_at DESC
                    LIMIT 10
                """, (symbol.upper(), time_window))
            else:
                cursor.execute("""
                    SELECT * FROM sentiment_results
                    WHERE time_window = %s
                    ORDER BY calculated_at DESC
                    LIMIT 50
                """, (time_window,))

            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error getting sentiment summary: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)

    def get_active_anomalies(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active anomalies"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            if symbol:
                cursor.execute("""
                    SELECT * FROM v_active_anomalies
                    WHERE symbol = %s
                    ORDER BY severity DESC, detected_at DESC
                """, (symbol.upper(),))
            else:
                cursor.execute("""
                    SELECT * FROM v_active_anomalies
                    ORDER BY severity DESC, detected_at DESC
                    LIMIT 50
                """)

            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error getting active anomalies: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)

    def get_ml_predictions(self, symbol: str, prediction_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get ML predictions for a cryptocurrency"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            if prediction_type:
                cursor.execute("""
                    SELECT * FROM ml_predictions
                    WHERE symbol = %s AND prediction_type = %s
                    AND (valid_until IS NULL OR valid_until > NOW())
                    ORDER BY predicted_at DESC
                    LIMIT 10
                """, (symbol.upper(), prediction_type))
            else:
                cursor.execute("""
                    SELECT * FROM ml_predictions
                    WHERE symbol = %s
                    AND (valid_until IS NULL OR valid_until > NOW())
                    ORDER BY predicted_at DESC
                    LIMIT 20
                """, (symbol.upper(),))

            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error getting ML predictions: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)

    def get_daily_sentiment(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily sentiment aggregation"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM v_daily_sentiment
                WHERE date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY date DESC, symbol ASC
            """, (days,))

            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error getting daily sentiment: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            stats = {}

            # Count records in each table
            tables = ['crypto_prices', 'crypto_news', 'social_posts',
                     'analytics_results', 'sentiment_results', 'ml_predictions', 'anomalies']

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cursor.fetchone()
                stats[f'{table}_count'] = result['count'] if result else 0

            # Get latest timestamps
            cursor.execute("SELECT MAX(timestamp) as latest FROM crypto_prices")
            result = cursor.fetchone()
            stats['latest_price_update'] = result['latest'].isoformat() if result and result['latest'] else None

            cursor.execute("SELECT MAX(published_at) as latest FROM crypto_news")
            result = cursor.fetchone()
            stats['latest_news_update'] = result['latest'].isoformat() if result and result['latest'] else None

            cursor.execute("SELECT MAX(published_at) as latest FROM social_posts")
            result = cursor.fetchone()
            stats['latest_social_update'] = result['latest'].isoformat() if result and result['latest'] else None

            return stats

        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
        finally:
            if conn:
                self.return_connection(conn)

    def get_news_sentiment_aggregated(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get aggregated sentiment from crypto_news table
        Returns sentiment metrics calculated from news articles
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cutoff = datetime.now() - timedelta(hours=hours)

            cursor.execute("""
                SELECT
                    'ALL' as symbol,
                    COUNT(*) as total_articles,
                    AVG(sentiment_score) as average_sentiment,
                    STDDEV(sentiment_score) as sentiment_stddev,
                    COUNT(CASE WHEN sentiment_label IN ('POSITIVE', 'positive') THEN 1 END) as positive_count,
                    COUNT(CASE WHEN sentiment_label IN ('NEGATIVE', 'negative') THEN 1 END) as negative_count,
                    COUNT(CASE WHEN sentiment_label IN ('NEUTRAL', 'neutral') THEN 1 END) as neutral_count,
                    COUNT(CASE WHEN analysis_method = 'ollama' THEN 1 END) as ollama_analyzed,
                    AVG(CASE WHEN confidence_score IS NOT NULL THEN confidence_score END) as avg_confidence,
                    NOW() as timestamp
                FROM crypto_news
                WHERE published_at >= %s
            """, (cutoff,))

            result = cursor.fetchone()
            if result:
                return [dict(result)]
            return []

        except Exception as e:
            logger.error(f"Error getting news sentiment aggregated: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)

    def get_news_sentiment_by_coin(self, hours: int = 24, min_mentions: int = 1) -> List[Dict[str, Any]]:
        """
        Get sentiment aggregated by mentioned coins from crypto_news
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cutoff = datetime.now() - timedelta(hours=hours)

            cursor.execute("""
                SELECT
                    UNNEST(mentioned_coins) as symbol,
                    COUNT(*) as mention_count,
                    AVG(sentiment_score) as average_sentiment,
                    COUNT(CASE WHEN sentiment_label IN ('POSITIVE', 'positive') THEN 1 END) as positive_count,
                    COUNT(CASE WHEN sentiment_label IN ('NEGATIVE', 'negative') THEN 1 END) as negative_count,
                    COUNT(CASE WHEN sentiment_label IN ('NEUTRAL', 'neutral') THEN 1 END) as neutral_count,
                    COUNT(CASE WHEN analysis_method = 'ollama' THEN 1 END) as ollama_analyzed,
                    AVG(CASE WHEN confidence_score IS NOT NULL THEN confidence_score END) as avg_confidence,
                    CASE
                        WHEN AVG(sentiment_score) > 0.1 THEN 'positive'
                        WHEN AVG(sentiment_score) < -0.1 THEN 'negative'
                        ELSE 'neutral'
                    END as dominant_sentiment,
                    NOW() as timestamp
                FROM crypto_news
                WHERE published_at >= %s
                  AND mentioned_coins IS NOT NULL
                  AND array_length(mentioned_coins, 1) > 0
                GROUP BY UNNEST(mentioned_coins)
                HAVING COUNT(*) >= %s
                ORDER BY mention_count DESC, average_sentiment DESC
                LIMIT 20
            """, (cutoff, min_mentions))

            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error getting news sentiment by coin: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)

    def get_news_sentiment_timeseries(self, hours: int = 24, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get sentiment time series data from crypto_news
        Returns sentiment aggregated by time intervals, optionally filtered by crypto symbol
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cutoff = datetime.now() - timedelta(hours=hours)

            # Build query with optional symbol filter
            if symbol:
                # Get the crypto name for this symbol
                cursor.execute("SELECT name FROM crypto_prices WHERE symbol = %s LIMIT 1", (symbol.upper(),))
                result = cursor.fetchone()
                crypto_name = result['name'] if result else symbol

                # Filter by title or description containing crypto name or symbol
                cursor.execute("""
                    SELECT
                        date_trunc('hour', published_at) as time_bucket,
                        COUNT(*) as article_count,
                        AVG(sentiment_score) as average_sentiment,
                        COUNT(CASE WHEN sentiment_label IN ('POSITIVE', 'positive') THEN 1 END) as positive_count,
                        COUNT(CASE WHEN sentiment_label IN ('NEGATIVE', 'negative') THEN 1 END) as negative_count,
                        COUNT(CASE WHEN sentiment_label IN ('NEUTRAL', 'neutral') THEN 1 END) as neutral_count,
                        COUNT(CASE WHEN analysis_method = 'ollama' THEN 1 END) as ollama_analyzed
                    FROM crypto_news
                    WHERE published_at >= %s
                      AND (
                        LOWER(title) LIKE %s
                        OR LOWER(description) LIKE %s
                        OR LOWER(title) LIKE %s
                        OR LOWER(description) LIKE %s
                      )
                    GROUP BY date_trunc('hour', published_at)
                    ORDER BY time_bucket ASC
                """, (cutoff, f'%{crypto_name.lower()}%', f'%{crypto_name.lower()}%', f'%{symbol.lower()}%', f'%{symbol.lower()}%'))
            else:
                cursor.execute("""
                    SELECT
                        date_trunc('hour', published_at) as time_bucket,
                        COUNT(*) as article_count,
                        AVG(sentiment_score) as average_sentiment,
                        COUNT(CASE WHEN sentiment_label IN ('POSITIVE', 'positive') THEN 1 END) as positive_count,
                        COUNT(CASE WHEN sentiment_label IN ('NEGATIVE', 'negative') THEN 1 END) as negative_count,
                        COUNT(CASE WHEN sentiment_label IN ('NEUTRAL', 'neutral') THEN 1 END) as neutral_count,
                        COUNT(CASE WHEN analysis_method = 'ollama' THEN 1 END) as ollama_analyzed
                    FROM crypto_news
                    WHERE published_at >= %s
                    GROUP BY date_trunc('hour', published_at)
                    ORDER BY time_bucket ASC
                """, (cutoff,))

            results = cursor.fetchall()
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error getting news sentiment timeseries: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)
