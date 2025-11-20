"""
CRYPTO VIZ - Analytics Service
Business logic layer for analytics operations
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from postgres_reader import PostgreSQLReader
from services.cache_service import get_cache

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service layer for analytics operations"""

    def __init__(self, pg_reader: PostgreSQLReader):
        """
        Initialize analytics service

        Args:
            pg_reader: PostgreSQL reader instance
        """
        self.pg_reader = pg_reader
        self.cache = get_cache()

    def get_price_analytics(self, symbol: str, timeframe: str = "1d",
                           limit: int = 100) -> Dict[str, Any]:
        """
        Get price analytics for a cryptocurrency

        Args:
            symbol: Cryptocurrency symbol
            timeframe: Time frame (1h, 4h, 1d, 7d, 30d)
            limit: Number of data points

        Returns:
            Analytics data with price history and metrics
        """
        # Try cache first
        cache_key = f"{symbol}:{timeframe}:{limit}"
        cached = self.cache.get("price_analytics", cache_key)
        if cached:
            return cached

        # Map timeframe to hours
        timeframe_hours = {
            "1h": 1,
            "4h": 4,
            "1d": 24,
            "7d": 168,
            "30d": 720
        }
        hours = timeframe_hours.get(timeframe, 24)

        # Get price history
        history = self.pg_reader.get_crypto_price_history(symbol, hours)

        if not history:
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "error": "No data available"
            }

        # Calculate analytics
        prices = [float(p['price']) for p in history if p.get('price')]
        if not prices:
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "error": "Invalid price data"
            }

        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "data_points": len(history),
            "history": history[:limit],
            "analytics": {
                "current_price": prices[-1] if prices else None,
                "min_price": min(prices),
                "max_price": max(prices),
                "avg_price": sum(prices) / len(prices),
                "price_change": prices[-1] - prices[0] if len(prices) > 1 else 0,
                "price_change_percent": ((prices[-1] - prices[0]) / prices[0] * 100) if len(prices) > 1 and prices[0] != 0 else 0,
                "volatility": self._calculate_volatility(prices)
            },
            "metadata": {
                "start_time": history[0]['timestamp'].isoformat() if history else None,
                "end_time": history[-1]['timestamp'].isoformat() if history else None,
                "calculated_at": datetime.utcnow().isoformat()
            }
        }

        # Cache for 2 minutes
        self.cache.set("price_analytics", cache_key, result, ttl=120)

        return result

    def get_market_overview(self) -> Dict[str, Any]:
        """
        Get market overview with top cryptocurrencies

        Returns:
            Market overview data
        """
        # Try cache first
        cached = self.cache.get("market", "overview")
        if cached:
            return cached

        # Get latest prices
        prices = self.pg_reader.get_latest_crypto_prices(limit=50)

        if not prices:
            return {"error": "No market data available"}

        # Calculate market statistics
        total_market_cap = sum(p.get('market_cap', 0) or 0 for p in prices)
        total_volume_24h = sum(p.get('volume_24h', 0) or 0 for p in prices)

        # Get sentiment data
        sentiment_data = self.pg_reader.get_sentiment_summary(time_window='24h')

        result = {
            "market_stats": {
                "total_market_cap": total_market_cap,
                "total_volume_24h": total_volume_24h,
                "total_cryptocurrencies": len(prices),
                "timestamp": datetime.utcnow().isoformat()
            },
            "top_gainers": self._get_top_movers(prices, "gainers", 10),
            "top_losers": self._get_top_movers(prices, "losers", 10),
            "top_by_volume": sorted(
                [p for p in prices if p.get('volume_24h')],
                key=lambda x: x.get('volume_24h', 0),
                reverse=True
            )[:10],
            "top_by_market_cap": sorted(
                [p for p in prices if p.get('market_cap')],
                key=lambda x: x.get('market_cap', 0),
                reverse=True
            )[:10],
            "overall_sentiment": self._calculate_overall_sentiment(sentiment_data) if sentiment_data else None
        }

        # Cache for 1 minute
        self.cache.set("market", "overview", result, ttl=60)

        return result

    def get_crypto_details(self, symbol: str) -> Dict[str, Any]:
        """
        Get detailed information about a cryptocurrency

        Args:
            symbol: Cryptocurrency symbol

        Returns:
            Detailed cryptocurrency information
        """
        # Try cache first
        cache_key = symbol
        cached = self.cache.get("crypto_details", cache_key)
        if cached:
            return cached

        # Get latest price
        prices = self.pg_reader.get_latest_crypto_prices(limit=100)
        crypto_price = next((p for p in prices if p['symbol'] == symbol.upper()), None)

        if not crypto_price:
            return {"error": f"Cryptocurrency {symbol} not found"}

        # Get additional data
        history_24h = self.pg_reader.get_crypto_price_history(symbol, hours=24)
        analytics = self.pg_reader.get_analytics_results(symbol=symbol, hours=24)
        sentiment = self.pg_reader.get_sentiment_summary(symbol=symbol, time_window='24h')
        predictions = self.pg_reader.get_ml_predictions(symbol=symbol)
        anomalies = self.pg_reader.get_active_anomalies(symbol=symbol)

        result = {
            "symbol": symbol.upper(),
            "current_data": crypto_price,
            "price_history_24h": history_24h,
            "analytics": analytics,
            "sentiment": sentiment[0] if sentiment else None,
            "predictions": predictions,
            "anomalies": anomalies,
            "metadata": {
                "retrieved_at": datetime.utcnow().isoformat()
            }
        }

        # Cache for 30 seconds
        self.cache.set("crypto_details", cache_key, result, ttl=30)

        return result

    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility (standard deviation)"""
        if len(prices) < 2:
            return 0.0

        mean = sum(prices) / len(prices)
        variance = sum((float(p) - mean) ** 2 for p in prices) / len(prices)
        return float(variance ** 0.5)

    def _get_top_movers(self, prices: List[Dict], direction: str, limit: int) -> List[Dict]:
        """Get top gainers or losers"""
        # Filter prices with 24h change
        with_change = [p for p in prices if p.get('percent_change_24h') is not None]

        if direction == "gainers":
            sorted_prices = sorted(with_change, key=lambda x: x.get('percent_change_24h', 0), reverse=True)
        else:  # losers
            sorted_prices = sorted(with_change, key=lambda x: x.get('percent_change_24h', 0))

        return sorted_prices[:limit]

    def _calculate_overall_sentiment(self, sentiment_data: List[Dict]) -> Dict[str, Any]:
        """Calculate overall market sentiment"""
        if not sentiment_data:
            return None

        total_positive = sum(s.get('positive_count', 0) for s in sentiment_data)
        total_negative = sum(s.get('negative_count', 0) for s in sentiment_data)
        total_neutral = sum(s.get('neutral_count', 0) for s in sentiment_data)
        total_count = total_positive + total_negative + total_neutral

        if total_count == 0:
            return None

        avg_score = sum(s.get('sentiment_score', 0) * s.get('total_count', 0) for s in sentiment_data) / total_count if total_count > 0 else 0

        return {
            "sentiment_score": round(avg_score, 3),
            "positive_count": total_positive,
            "negative_count": total_negative,
            "neutral_count": total_neutral,
            "total_count": total_count,
            "positive_percent": round(total_positive / total_count * 100, 2) if total_count > 0 else 0,
            "negative_percent": round(total_negative / total_count * 100, 2) if total_count > 0 else 0,
            "neutral_percent": round(total_neutral / total_count * 100, 2) if total_count > 0 else 0
        }
