#!/usr/bin/env python3
"""
Prediction Service
Manages ML predictions with caching for performance
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import OrderedDict
from postgres_reader import PostgreSQLReader

logger = logging.getLogger(__name__)


class LRUCache:
    """Simple LRU cache implementation with TTL"""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        """Initialize LRU cache"""
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.timestamps = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            return None

        # Check if expired
        if datetime.now() - self.timestamps[key] > timedelta(seconds=self.ttl_seconds):
            self.cache.pop(key)
            self.timestamps.pop(key)
            return None

        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key: str, value: Any):
        """Set value in cache"""
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        self.timestamps[key] = datetime.now()

        # Remove oldest if over max size
        if len(self.cache) > self.max_size:
            oldest_key = next(iter(self.cache))
            self.cache.pop(oldest_key)
            self.timestamps.pop(oldest_key)

    def invalidate(self, key: str):
        """Invalidate a specific key"""
        if key in self.cache:
            self.cache.pop(key)
            self.timestamps.pop(key)

    def clear(self):
        """Clear entire cache"""
        self.cache.clear()
        self.timestamps.clear()


class PredictionService:
    """Service for handling ML predictions with caching"""

    def __init__(self, postgres_reader: Optional[PostgreSQLReader] = None):
        """Initialize prediction service"""
        self.pg_reader = postgres_reader or PostgreSQLReader()
        self.cache = LRUCache(max_size=100, ttl_seconds=300)  # 5 minute TTL
        logger.info("Prediction Service initialized with LRU cache")

    def get_predictions(
        self,
        symbol: Optional[str] = None,
        prediction_type: str = "price",
        hours_ahead: Optional[int] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get ML predictions with caching

        Args:
            symbol: Cryptocurrency symbol (None for all)
            prediction_type: Type of prediction ('price', 'volatility', 'trend')
            hours_ahead: Filter by prediction horizon
            use_cache: Whether to use cache

        Returns:
            List of predictions
        """
        # Generate cache key
        cache_key = f"predictions:{symbol}:{prediction_type}:{hours_ahead}"

        # Check cache
        if use_cache:
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

        conn = None
        try:
            conn = self.pg_reader.get_connection()
            cursor = conn.cursor()

            # Build query
            query = """
                SELECT
                    id,
                    symbol,
                    prediction_type,
                    predicted_value,
                    confidence,
                    predicted_at,
                    valid_until,
                    model_name,
                    model_version,
                    rmse,
                    r2_score,
                    features_used,
                    metadata
                FROM v_latest_predictions
                WHERE 1=1
            """
            params = []

            if symbol:
                query += " AND symbol = %s"
                params.append(symbol.upper())

            if prediction_type:
                query += " AND prediction_type = %s"
                params.append(prediction_type)

            query += " ORDER BY predicted_at DESC"

            cursor.execute(query, params)
            predictions = cursor.fetchall()

            # Filter by hours_ahead if specified
            if hours_ahead is not None:
                predictions = [
                    p for p in predictions
                    if p.get('metadata') and p['metadata'].get('horizon_hours') == hours_ahead
                ]

            # Format results
            result = [{
                'id': str(p['id']),
                'symbol': p['symbol'],
                'prediction_type': p['prediction_type'],
                'predicted_value': float(p['predicted_value']),
                'confidence': float(p['confidence']) if p['confidence'] else None,
                'predicted_at': p['predicted_at'].isoformat() if p['predicted_at'] else None,
                'valid_until': p['valid_until'].isoformat() if p['valid_until'] else None,
                'model_name': p['model_name'],
                'model_version': p['model_version'],
                'rmse': float(p['rmse']) if p['rmse'] else None,
                'r2_score': float(p['r2_score']) if p['r2_score'] else None,
                'features_used': p['features_used'],
                'metadata': p['metadata']
            } for p in predictions]

            # Cache result
            if use_cache:
                self.cache.set(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Error getting predictions: {e}")
            return []
        finally:
            if conn:
                self.pg_reader.return_connection(conn)

    def get_prediction_accuracy(self, symbol: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
        """
        Get historical prediction accuracy metrics

        Args:
            symbol: Cryptocurrency symbol (None for all)
            days: Number of days to look back

        Returns:
            Dictionary with accuracy metrics
        """
        conn = None
        try:
            conn = self.pg_reader.get_connection()
            cursor = conn.cursor()

            # Get predictions from last N days
            cutoff = datetime.now() - timedelta(days=days)

            query = """
                SELECT
                    symbol,
                    prediction_type,
                    AVG(CASE WHEN confidence IS NOT NULL THEN confidence ELSE 0 END) as avg_confidence,
                    AVG(CASE WHEN rmse IS NOT NULL THEN rmse ELSE 0 END) as avg_rmse,
                    AVG(CASE WHEN r2_score IS NOT NULL THEN r2_score ELSE 0 END) as avg_r2_score,
                    COUNT(*) as prediction_count,
                    model_name,
                    model_version
                FROM ml_predictions
                WHERE predicted_at >= %s
            """
            params = [cutoff]

            if symbol:
                query += " AND symbol = %s"
                params.append(symbol.upper())

            query += """
                GROUP BY symbol, prediction_type, model_name, model_version
                ORDER BY symbol, prediction_type
            """

            cursor.execute(query, params)
            accuracy_data = cursor.fetchall()

            return {
                'period_days': days,
                'symbol': symbol,
                'accuracy_by_symbol': [{
                    'symbol': a['symbol'],
                    'prediction_type': a['prediction_type'],
                    'avg_confidence': float(a['avg_confidence']),
                    'avg_rmse': float(a['avg_rmse']),
                    'avg_r2_score': float(a['avg_r2_score']),
                    'prediction_count': a['prediction_count'],
                    'model_name': a['model_name'],
                    'model_version': a['model_version']
                } for a in accuracy_data]
            }

        except Exception as e:
            logger.error(f"Error getting prediction accuracy: {e}")
            return {
                'period_days': days,
                'symbol': symbol,
                'accuracy_by_symbol': [],
                'error': str(e)
            }
        finally:
            if conn:
                self.pg_reader.return_connection(conn)

    def invalidate_predictions(self, symbol: Optional[str] = None):
        """
        Invalidate prediction cache

        Args:
            symbol: Symbol to invalidate (None to clear all)
        """
        if symbol is None:
            self.cache.clear()
            logger.info("Cleared entire prediction cache")
        else:
            # Invalidate all cache keys for this symbol
            keys_to_invalidate = [k for k in self.cache.cache.keys() if symbol.upper() in k]
            for key in keys_to_invalidate:
                self.cache.invalidate(key)
            logger.info(f"Invalidated {len(keys_to_invalidate)} cache entries for {symbol}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cache_size': len(self.cache.cache),
            'max_size': self.cache.max_size,
            'ttl_seconds': self.cache.ttl_seconds,
            'cached_keys': list(self.cache.cache.keys())
        }


# Singleton instance
_prediction_service = None


def get_prediction_service() -> PredictionService:
    """Get singleton prediction service instance"""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service
