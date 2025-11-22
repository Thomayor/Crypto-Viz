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
            SELECT id, symbol, predicted_value, confidence, prediction_type,
                   predicted_at, valid_until, model_name, model_version, rmse, r2_score
            FROM ml_predictions
            WHERE valid_until > NOW()
            ORDER BY predicted_at DESC
            LIMIT {limit}
        """
        results = pg_reader.query(query)

        # Group by symbol
        predictions_by_coin = {}
        for row in results:
            coin = row['symbol']
            if coin not in predictions_by_coin:
                predictions_by_coin[coin] = []
            predictions_by_coin[coin].append({
                "id": str(row['id']) if row.get('id') else None,
                "symbol": row['symbol'],
                "predicted_value": float(row['predicted_value']) if row['predicted_value'] else 0,
                "confidence": float(row['confidence']) if row['confidence'] else 0,
                "prediction_type": row['prediction_type'] or "price",
                "predicted_at": row['predicted_at'].isoformat() if row['predicted_at'] else datetime.now().isoformat(),
                "valid_until": row['valid_until'].isoformat() if row.get('valid_until') else None,
                "model_name": row.get('model_name') or "Unknown",
                "model_version": row.get('model_version'),
                "rmse": float(row['rmse']) if row.get('rmse') else None,
                "r2_score": float(row['r2_score']) if row.get('r2_score') else None
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
            SELECT id, symbol, anomaly_type, severity, description, anomaly_score, detected_at
            FROM anomalies
            WHERE is_resolved = FALSE {severity_filter}
            ORDER BY detected_at DESC
            LIMIT {limit}
        """

        results = pg_reader.query(query)

        anomalies = []
        for row in results:
            # Create metadata with extra fields
            metadata = {
                "id": str(row['id']),
                "anomaly_score": float(row['anomaly_score']) if row['anomaly_score'] else 0.0
            }

            anomalies.append(Anomaly(
                symbol=row['symbol'],
                anomaly_type=row['anomaly_type'] or "unknown",
                severity=row['severity'] or "medium",
                description=row['description'] or "Anomaly detected",
                detected_at=row['detected_at'] if row['detected_at'] else datetime.now(),
                metadata=metadata
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

        # Transform to match frontend expected format
        sentiment_data = []

        # If a specific symbol is requested, only return data for that symbol
        if symbol:
            # Get time series data for the specific symbol
            timeseries = pg_reader.get_news_sentiment_timeseries(hours=hours, symbol=symbol)

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
                    "symbol": symbol.upper(),
                    "time_window": f"{hours}h",
                    "average_sentiment": avg_sent,
                    "positive_count": int(ts.get('positive_count', 0)),
                    "negative_count": int(ts.get('negative_count', 0)),
                    "neutral_count": int(ts.get('neutral_count', 0)),
                    "total_count": int(ts.get('article_count', 0)),
                    "ollama_analyzed": int(ts.get('ollama_analyzed', 0)),
                    "avg_confidence": float(ts.get('avg_confidence', 0.0)) if ts.get('avg_confidence') else None,
                    "dominant_sentiment": dominant,
                    "timestamp": ts.get('time_bucket').isoformat() if ts.get('time_bucket') else datetime.now().isoformat()
                })
        else:
            # Get all data when no symbol is specified
            # Get time series data for the chart
            timeseries = pg_reader.get_news_sentiment_timeseries(hours=hours, symbol=None)

            # Get aggregated sentiment from news
            overall_sentiment = pg_reader.get_news_sentiment_aggregated(hours=hours)

            # Get sentiment by coin
            by_coin_sentiment = pg_reader.get_news_sentiment_by_coin(hours=hours, min_mentions=2)

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
                    "avg_confidence": float(ts.get('avg_confidence', 0.0)) if ts.get('avg_confidence') else None,
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


# ========================================
# ML ANALYTICS ENDPOINTS
# (Defined BEFORE generic /{symbol} routes to ensure proper routing)
# ========================================

# Import ML services
from services.ml import (
    get_clustering_service,
    get_prediction_service,
    get_correlation_service,
    get_anomaly_detector
)


@router.get("/ml/clusters", summary="Get all cluster assignments")
async def get_all_clusters():
    """
    Get all current cryptocurrency cluster assignments

    Returns:
    - List of all clusters with assignments
    """
    try:
        clustering_service = get_clustering_service()
        return clustering_service.get_all_clusters()
    except Exception as e:
        logger.error(f"Error getting all clusters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/clusters/statistics", summary="Get cluster statistics")
async def get_cluster_statistics():
    """
    Get overall clustering statistics

    Returns:
    - Total cryptos clustered
    - Number of clusters
    - Overall silhouette score
    - Cluster distribution
    """
    try:
        clustering_service = get_clustering_service()
        return clustering_service.get_cluster_statistics()
    except Exception as e:
        logger.error(f"Error getting cluster statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/clusters/{cluster_id}", summary="Get cluster insights")
async def get_cluster_insights(cluster_id: int):
    """
    Get detailed insights for a specific cluster

    - **cluster_id**: Cluster ID to analyze

    Returns:
    - Cluster label and characteristics
    - List of cryptocurrencies in cluster
    - Average features
    """
    try:
        clustering_service = get_clustering_service()
        return clustering_service.get_cluster_insights(cluster_id)
    except Exception as e:
        logger.error(f"Error getting cluster insights for {cluster_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/similar/{symbol}", summary="Get similar cryptocurrencies")
async def get_similar_cryptos(symbol: str, limit: int = 5):
    """
    Get cryptocurrencies similar to the given symbol (same cluster)

    - **symbol**: Cryptocurrency symbol
    - **limit**: Maximum number of similar cryptos to return (default: 5)

    Returns:
    - List of similar cryptocurrencies with cluster info
    """
    try:
        clustering_service = get_clustering_service()
        return clustering_service.get_similar_cryptos(symbol, limit)
    except Exception as e:
        logger.error(f"Error getting similar cryptos for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/predictions", summary="Get ML predictions")
async def get_ml_predictions(
    symbol: Optional[str] = None,
    prediction_type: str = "price",
    hours_ahead: Optional[int] = None,
    use_cache: bool = True
):
    """
    Get ML predictions with caching

    - **symbol**: Cryptocurrency symbol (optional, None for all)
    - **prediction_type**: Type of prediction ('price', 'volatility', 'trend')
    - **hours_ahead**: Filter by prediction horizon (optional)
    - **use_cache**: Use cached predictions (default: true)

    Returns:
    - List of ML predictions with confidence scores
    """
    try:
        prediction_service = get_prediction_service()
        return prediction_service.get_predictions(
            symbol=symbol,
            prediction_type=prediction_type,
            hours_ahead=hours_ahead,
            use_cache=use_cache
        )
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/predictions/accuracy", summary="Get prediction accuracy metrics")
async def get_prediction_accuracy(
    symbol: Optional[str] = None,
    days: int = 7
):
    """
    Get historical prediction accuracy metrics

    - **symbol**: Cryptocurrency symbol (optional, None for all)
    - **days**: Number of days to analyze (default: 7)

    Returns:
    - Accuracy metrics (avg confidence, RMSE, R² score)
    """
    try:
        prediction_service = get_prediction_service()
        return prediction_service.get_prediction_accuracy(symbol, days)
    except Exception as e:
        logger.error(f"Error getting prediction accuracy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml/predictions/invalidate", summary="Invalidate prediction cache")
async def invalidate_prediction_cache(symbol: Optional[str] = None):
    """
    Invalidate prediction cache for a symbol or all symbols

    - **symbol**: Symbol to invalidate (optional, None to clear all)

    Returns:
    - Success message
    """
    try:
        prediction_service = get_prediction_service()
        prediction_service.invalidate_predictions(symbol)
        return {"message": f"Cache invalidated for {symbol if symbol else 'all symbols'}"}
    except Exception as e:
        logger.error(f"Error invalidating prediction cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/correlations/matrix", summary="Get correlation matrix")
async def get_correlation_matrix(
    symbols: Optional[str] = None,
    time_window: str = "7d",
    min_coefficient: Optional[float] = None
):
    """
    Get correlation matrix for specified symbols

    - **symbols**: Comma-separated list of symbols (optional, None for all)
    - **time_window**: Time window ('1d', '7d', '30d', default: '7d')
    - **min_coefficient**: Minimum correlation coefficient to include (optional)

    Returns:
    - Correlation matrix data
    """
    try:
        correlation_service = get_correlation_service()
        symbol_list = symbols.split(',') if symbols else None
        return correlation_service.get_correlation_matrix(
            symbols=symbol_list,
            time_window=time_window,
            min_coefficient=min_coefficient
        )
    except Exception as e:
        logger.error(f"Error getting correlation matrix: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/correlations/{symbol}", summary="Get top correlations for symbol")
async def get_top_correlations(
    symbol: str,
    limit: int = 10,
    time_window: str = "7d",
    positive_only: bool = False
):
    """
    Get top correlations for a specific symbol

    - **symbol**: Cryptocurrency symbol
    - **limit**: Maximum number of correlations (default: 10)
    - **time_window**: Time window ('1d', '7d', '30d', default: '7d')
    - **positive_only**: Only return positive correlations (default: false)

    Returns:
    - List of top correlated pairs
    """
    try:
        correlation_service = get_correlation_service()
        return correlation_service.get_top_correlations(
            symbol=symbol,
            limit=limit,
            time_window=time_window,
            positive_only=positive_only
        )
    except Exception as e:
        logger.error(f"Error getting top correlations for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/correlations/{symbol}/inverse", summary="Get inverse correlations for hedging")
async def get_inverse_correlations(
    symbol: str,
    limit: int = 10,
    time_window: str = "7d",
    min_coefficient: float = -0.5
):
    """
    Get inverse (negative) correlations for hedging opportunities

    - **symbol**: Cryptocurrency symbol
    - **limit**: Maximum number of correlations (default: 10)
    - **time_window**: Time window ('1d', '7d', '30d', default: '7d')
    - **min_coefficient**: Minimum negative correlation (default: -0.5)

    Returns:
    - List of inversely correlated pairs for hedging
    """
    try:
        correlation_service = get_correlation_service()
        return correlation_service.get_inverse_correlations(
            symbol=symbol,
            limit=limit,
            time_window=time_window,
            min_coefficient=min_coefficient
        )
    except Exception as e:
        logger.error(f"Error getting inverse correlations for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/correlations/statistics", summary="Get correlation statistics")
async def get_correlation_statistics(time_window: str = "7d"):
    """
    Get overall correlation statistics

    - **time_window**: Time window ('1d', '7d', '30d', default: '7d')

    Returns:
    - Overall correlation statistics by strength
    """
    try:
        correlation_service = get_correlation_service()
        return correlation_service.get_correlation_statistics(time_window)
    except Exception as e:
        logger.error(f"Error getting correlation statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/anomalies", summary="Get active anomalies")
async def get_active_anomalies_ml(
    severity: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = 50
):
    """
    Get currently active (unresolved) anomalies

    - **severity**: Filter by severity ('low', 'medium', 'high', 'critical')
    - **symbol**: Filter by cryptocurrency symbol
    - **limit**: Maximum number of anomalies (default: 50)

    Returns:
    - List of active anomalies
    """
    try:
        anomaly_detector = get_anomaly_detector()
        return anomaly_detector.get_active_anomalies(
            severity_filter=severity,
            symbol=symbol,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error getting active anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/anomalies/history", summary="Get anomaly history")
async def get_anomaly_history(
    symbol: Optional[str] = None,
    days: int = 7,
    include_resolved: bool = True
):
    """
    Get historical anomalies

    - **symbol**: Filter by cryptocurrency symbol
    - **days**: Number of days to look back (default: 7)
    - **include_resolved**: Include resolved anomalies (default: true)

    Returns:
    - List of historical anomalies
    """
    try:
        anomaly_detector = get_anomaly_detector()
        return anomaly_detector.get_anomaly_history(
            symbol=symbol,
            days=days,
            include_resolved=include_resolved
        )
    except Exception as e:
        logger.error(f"Error getting anomaly history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ml/anomalies/statistics", summary="Get anomaly statistics")
async def get_anomaly_statistics(days: int = 30):
    """
    Get anomaly detection statistics

    - **days**: Number of days to analyze (default: 30)

    Returns:
    - Comprehensive anomaly statistics
    """
    try:
        anomaly_detector = get_anomaly_detector()
        return anomaly_detector.get_anomaly_statistics(days)
    except Exception as e:
        logger.error(f"Error getting anomaly statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml/anomalies/{anomaly_id}/resolve", summary="Resolve an anomaly")
async def resolve_anomaly(
    anomaly_id: str,
    resolution_notes: Optional[str] = None
):
    """
    Mark an anomaly as resolved

    - **anomaly_id**: UUID of the anomaly
    - **resolution_notes**: Optional notes about the resolution

    Returns:
    - Success message
    """
    try:
        anomaly_detector = get_anomaly_detector()
        success = anomaly_detector.resolve_anomaly(anomaly_id, resolution_notes)

        if success:
            return {"message": f"Anomaly {anomaly_id} resolved successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Anomaly {anomaly_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving anomaly {anomaly_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# GENERIC SYMBOL-BASED ENDPOINTS
# (Defined AFTER /ml/* routes to avoid conflicts)
# ========================================

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
