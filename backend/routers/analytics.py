"""
CRYPTO VIZ - Analytics Router
REST API endpoints for cryptocurrency analytics
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from models.crypto_models import AnalyticsResult, MLPrediction, Anomaly, ErrorResponse
from services.analytics_service import AnalyticsService
from services.cache_service import get_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

# Global instances - will be set by main.py
_pg_reader = None
_analytics_service = None


def set_pg_reader(pg_reader):
    """Set the PostgreSQL reader instance"""
    global _pg_reader, _analytics_service
    _pg_reader = pg_reader
    _analytics_service = AnalyticsService(pg_reader)


def get_analytics_service() -> AnalyticsService:
    """Get the analytics service instance"""
    if _analytics_service is None:
        raise HTTPException(status_code=500, detail="Analytics service not initialized")
    return _analytics_service


def get_pg_reader():
    """Get the PostgreSQL reader instance"""
    if _pg_reader is None:
        raise HTTPException(status_code=500, detail="Database reader not initialized")
    return _pg_reader


@router.get("/all/predictions", response_model=dict, summary="Get all ML predictions")
async def get_all_predictions(
    limit: int = Query(default=100, ge=1, le=500, description="Number of predictions per symbol")
):
    """Get ML predictions for all cryptocurrencies"""
    try:
        pg_reader = get_pg_reader()
        query = f"""
            SELECT coin_id, predicted_price, confidence, model_type, timestamp
            FROM ml_predictions
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        results = pg_reader.query(query)

        # Group by coin_id
        predictions_by_coin = {}
        for row in results:
            coin = row[0]
            if coin not in predictions_by_coin:
                predictions_by_coin[coin] = []
            predictions_by_coin[coin].append({
                "coin_id": row[0],
                "predicted_price": float(row[1]) if row[1] else 0,
                "confidence": float(row[2]) if row[2] else 0,
                "model_type": row[3] or "LinearRegression",
                "timestamp": row[4].isoformat() if row[4] else datetime.now().isoformat()
            })

        return predictions_by_coin
    except Exception as e:
        logger.error(f"Error fetching all predictions: {e}")
        return {}


@router.get("/all/anomalies", response_model=List[Anomaly], summary="Get all detected anomalies")
async def get_all_anomalies(
    severity: Optional[str] = Query(default=None, description="Filter by severity"),
    limit: int = Query(default=100, ge=1, le=500, description="Number of anomalies")
):
    """Get detected anomalies for all cryptocurrencies"""
    try:
        pg_reader = get_pg_reader()

        severity_filter = f"AND severity = '{severity}'" if severity else ""
        query = f"""
            SELECT id, coin_id, anomaly_type, severity, description, anomaly_score, timestamp
            FROM anomalies
            WHERE 1=1 {severity_filter}
            ORDER BY timestamp DESC
            LIMIT {limit}
        """

        results = pg_reader.query(query)

        anomalies = []
        for row in results:
            anomalies.append(Anomaly(
                id=str(row[0]),
                coin_id=row[1],
                anomaly_type=row[2] or "unknown",
                severity=row[3] or "medium",
                description=row[4] or "Anomaly detected",
                anomaly_score=float(row[5]) if row[5] else 0.0,
                timestamp=row[6].isoformat() if row[6] else datetime.now().isoformat()
            ))

        return anomalies
    except Exception as e:
        logger.error(f"Error fetching all anomalies: {e}")
        return []


@router.get("/all/sentiment", summary="Get overall sentiment data")
async def get_all_sentiment(
    hours: int = Query(default=24, ge=1, le=168, description="Number of hours to analyze"),
    symbol: Optional[str] = Query(default=None, description="Filter by cryptocurrency symbol (e.g., BTC, ETH)")
):
    """
    Get sentiment analysis aggregated from crypto news

    Returns sentiment metrics calculated from news articles analyzed by Ollama
    Optionally filter by cryptocurrency symbol
    """
    try:
        pg_reader = get_pg_reader()

        # Get time series data for the chart (filtered by symbol if provided)
        timeseries = pg_reader.get_news_sentiment_timeseries(hours=hours, symbol=symbol)

        # Get aggregated sentiment from news
        overall_sentiment = pg_reader.get_news_sentiment_aggregated(hours=hours)

        # Get sentiment by coin
        by_coin_sentiment = pg_reader.get_news_sentiment_by_coin(hours=hours, min_mentions=2)

        # Transform to match frontend expected format
        sentiment_data = []

        # Add time series data points for the chart
        for ts in timeseries:
            avg_sent = float(ts.get('average_sentiment', 0.0))
            # Determine dominant sentiment
            if avg_sent > 0.1:
                dominant = 'positive'
            elif avg_sent < -0.1:
                dominant = 'negative'
            else:
                dominant = 'neutral'

            sentiment_data.append({
                "symbol": "ALL",
                "time_window": f"{hours}h",
                "average_sentiment": avg_sent,
                "positive_count": int(ts.get('positive_count', 0)),
                "negative_count": int(ts.get('negative_count', 0)),
                "neutral_count": int(ts.get('neutral_count', 0)),
                "total_count": int(ts.get('article_count', 0)),
                "ollama_analyzed": int(ts.get('ollama_analyzed', 0)),
                "dominant_sentiment": dominant,
                "timestamp": ts.get('time_bucket').isoformat() if ts.get('time_bucket') else datetime.now().isoformat()
            })

        # If no timeseries data, add overall as fallback
        if not sentiment_data and overall_sentiment:
            overall = overall_sentiment[0]
            avg_sent = float(overall.get('average_sentiment', 0.0))
            # Determine dominant sentiment
            if avg_sent > 0.1:
                dominant = 'positive'
            elif avg_sent < -0.1:
                dominant = 'negative'
            else:
                dominant = 'neutral'

            sentiment_data.append({
                "symbol": "ALL",
                "time_window": f"{hours}h",
                "average_sentiment": avg_sent,
                "positive_count": int(overall.get('positive_count', 0)),
                "negative_count": int(overall.get('negative_count', 0)),
                "neutral_count": int(overall.get('neutral_count', 0)),
                "total_count": int(overall.get('total_articles', 0)),
                "ollama_analyzed": int(overall.get('ollama_analyzed', 0)),
                "avg_confidence": float(overall.get('avg_confidence', 0.0)) if overall.get('avg_confidence') else None,
                "dominant_sentiment": dominant,
                "timestamp": overall.get('timestamp').isoformat() if overall.get('timestamp') else datetime.now().isoformat()
            })

        # Add by-coin data
        for coin in by_coin_sentiment:
            sentiment_data.append({
                "symbol": coin.get('symbol'),
                "time_window": f"{hours}h",
                "average_sentiment": float(coin.get('average_sentiment', 0.0)),
                "positive_count": int(coin.get('positive_count', 0)),
                "negative_count": int(coin.get('negative_count', 0)),
                "neutral_count": int(coin.get('neutral_count', 0)),
                "total_count": int(coin.get('mention_count', 0)),
                "ollama_analyzed": int(coin.get('ollama_analyzed', 0)),
                "avg_confidence": float(coin.get('avg_confidence', 0.0)) if coin.get('avg_confidence') else None,
                "dominant_sentiment": coin.get('dominant_sentiment'),
                "timestamp": coin.get('timestamp').isoformat() if coin.get('timestamp') else datetime.now().isoformat()
            })

        return sentiment_data
    except Exception as e:
        logger.error(f"Error fetching sentiment data: {e}")
        return []


@router.get("/{symbol}", summary="Get analytics data for cryptocurrency")
async def get_analytics_by_symbol(
    symbol: str,
    timeframe: str = Query(default="1d", description="Timeframe: 1h, 4h, 1d, 7d, 30d"),
    limit: int = Query(default=100, ge=1, le=500, description="Number of data points")
):
    """
    Get comprehensive analytics data for a cryptocurrency

    - **symbol**: Cryptocurrency symbol (e.g., BTC, ETH)
    - **timeframe**: Time frame (1h, 4h, 1d, 7d, 30d)
    - **limit**: Number of data points to return (1-500)

    Returns historical data with calculated analytics (volatility, trends, etc.)
    """
    try:
        analytics_service = get_analytics_service()
        result = analytics_service.get_price_analytics(symbol, timeframe, limit)

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analytics: {str(e)}")


@router.get("/{symbol}/metrics", summary="Get technical metrics")
async def get_technical_metrics(
    symbol: str,
    metric_type: Optional[str] = Query(default=None, description="Metric type filter"),
    hours: int = Query(default=24, ge=1, le=168, description="Time window in hours")
):
    """
    Get technical analysis metrics for a cryptocurrency

    - **symbol**: Cryptocurrency symbol
    - **metric_type**: Filter by metric type (volatility, correlation, ma, rsi, etc.)
    - **hours**: Time window in hours (1-168)

    Returns technical indicators and metrics calculated by analytics engine
    """
    cache = get_cache()
    cache_key = f"{symbol.upper()}:{metric_type or 'all'}:{hours}"

    # Try cache first
    cached = cache.get("metrics", cache_key)
    if cached:
        return cached

    try:
        pg_reader = get_pg_reader()
        metrics = pg_reader.get_analytics_results(
            symbol=symbol,
            metric_type=metric_type,
            hours=hours
        )

        if not metrics:
            raise HTTPException(
                status_code=404,
                detail=f"No metrics found for '{symbol}'"
            )

        result = {
            "symbol": symbol.upper(),
            "metric_type": metric_type or "all",
            "time_window": f"{hours}h",
            "count": len(metrics),
            "metrics": metrics
        }

        # Cache for 1 minute
        cache.set("metrics", cache_key, result, ttl=60)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


@router.get("/{symbol}/predictions", response_model=List[MLPrediction], summary="Get ML predictions")
async def get_predictions(
    symbol: str,
    prediction_type: Optional[str] = Query(default=None, description="Prediction type: price, volatility, trend")
):
    """
    Get machine learning predictions for a cryptocurrency

    - **symbol**: Cryptocurrency symbol
    - **prediction_type**: Type of prediction (price, volatility, trend)

    Returns ML model predictions with confidence scores
    """
    cache = get_cache()
    cache_key = f"{symbol.upper()}:{prediction_type or 'all'}"

    # Try cache first
    cached = cache.get("predictions", cache_key)
    if cached:
        return cached

    try:
        pg_reader = get_pg_reader()
        predictions = pg_reader.get_ml_predictions(symbol, prediction_type)

        if not predictions:
            raise HTTPException(
                status_code=404,
                detail=f"No predictions found for '{symbol}'"
            )

        # Cache for 2 minutes
        cache.set("predictions", cache_key, predictions, ttl=120)

        return predictions

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting predictions for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve predictions: {str(e)}")


@router.get("/{symbol}/anomalies", response_model=List[Anomaly], summary="Get detected anomalies")
async def get_anomalies(
    symbol: str
):
    """
    Get active anomalies detected for a cryptocurrency

    - **symbol**: Cryptocurrency symbol

    Returns list of detected anomalies (price spikes, unusual volume, etc.)
    """
    cache = get_cache()
    cache_key = symbol.upper()

    # Try cache first
    cached = cache.get("anomalies", cache_key)
    if cached:
        return cached

    try:
        pg_reader = get_pg_reader()
        anomalies = pg_reader.get_active_anomalies(symbol=symbol)

        # Cache for 30 seconds
        cache.set("anomalies", cache_key, anomalies, ttl=30)

        return anomalies

    except Exception as e:
        logger.error(f"Error getting anomalies for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve anomalies: {str(e)}")


@router.get("/{symbol}/detailed", summary="Get detailed crypto information")
async def get_detailed_info(
    symbol: str
):
    """
    Get comprehensive detailed information for a cryptocurrency

    - **symbol**: Cryptocurrency symbol

    Returns:
    - Current price data
    - 24h price history
    - Analytics metrics
    - Sentiment analysis
    - ML predictions
    - Active anomalies
    """
    try:
        analytics_service = get_analytics_service()
        result = analytics_service.get_crypto_details(symbol)

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting detailed info for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve detailed information: {str(e)}")
