#!/usr/bin/env python3
"""
CRYPTO VIZ - Backend API
FastAPI backend with modular structure and PostgreSQL integration
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
import logging
from contextlib import asynccontextmanager

# Import configuration
from config import settings, get_logging_config

# Import routers
from routers.health import router as health_router, set_pg_reader as set_health_pg_reader
from routers.prices import router as prices_router, set_pg_reader as set_prices_pg_reader
from routers.analytics import router as analytics_router, set_pg_reader as set_analytics_pg_reader
from routers.sentiment import router as sentiment_router, set_pg_reader as set_sentiment_pg_reader
from routers.news import router as news_router, set_pg_reader as set_news_pg_reader
from routers.markets import router as markets_router, set_pg_reader as set_markets_pg_reader
from routers.websocket import router as websocket_router, start_websocket_service, stop_websocket_service

# Import database reader
from postgres_reader import PostgreSQLReader

# Import services
from services.cache_service import get_cache, close_cache

# Configure logging
logging.config.dictConfig(get_logging_config())
logger = logging.getLogger(__name__)

# PostgreSQL reader instance (global)
pg_reader = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    global pg_reader
    try:
        pg_reader = PostgreSQLReader(
            min_conn=settings.postgres_min_conn,
            max_conn=settings.postgres_max_conn
        )
        # Set pg_reader for all routers
        set_health_pg_reader(pg_reader)
        set_prices_pg_reader(pg_reader)
        set_analytics_pg_reader(pg_reader)
        set_sentiment_pg_reader(pg_reader)
        set_news_pg_reader(pg_reader)
        set_markets_pg_reader(pg_reader)
        logger.info("✓ PostgreSQL reader initialized")

        # Initialize cache
        cache = get_cache()
        logger.info(f"✓ Redis cache initialized: {cache.get_stats()}")

        # Start WebSocket service (Kafka consumers + heartbeat)
        await start_websocket_service()

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        logger.warning("API will start but some features may fail")

    yield

    # Shutdown
    # Stop WebSocket service
    await stop_websocket_service()

    if pg_reader:
        pg_reader.close_all()
        logger.info("PostgreSQL connections closed")

    # Close cache
    close_cache()
    logger.info("Cache connections closed")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Include routers
app.include_router(health_router)
app.include_router(prices_router)
app.include_router(analytics_router)  # ✓ No conflicts - router only has /all/* and /{symbol}/* paths
app.include_router(sentiment_router)
# app.include_router(news_router)  # Conflicts: /latest
app.include_router(markets_router)
app.include_router(websocket_router)

logger.info(f"CORS enabled for origins: {settings.cors_origins_list}")
logger.info("✓ All routers registered: /health, /api/prices, /api/analytics, /api/sentiment, /api/news, /api/markets, /ws")


# =====================================
# CRYPTO PRICES ENDPOINTS
# =====================================

@app.get("/api/crypto/latest", tags=["Cryptocurrency Prices"])
async def get_latest_crypto(limit: int = Query(default=10, ge=1, le=100)):
    """
    Get latest cryptocurrency prices

    Returns the most recent price data for cryptocurrencies.

    **Query Parameters:**
    - **limit**: Number of cryptocurrencies to return (1-100, default: 10)

    **Returns:**
    - List of cryptocurrency price records with symbol, name, price, 24h change, volume, market cap
    """
    if not pg_reader:
        # Fallback to mock data if DB not available
        return [
            {"symbol": "BTC", "name": "Bitcoin", "price": "45000", "change": "2.5", "volume": "1.2B"},
            {"symbol": "ETH", "name": "Ethereum", "price": "3200", "change": "-1.2", "volume": "800M"},
            {"symbol": "ADA", "name": "Cardano", "price": "1.20", "change": "5.8", "volume": "300M"}
        ]

    try:
        prices = pg_reader.get_latest_crypto_prices(limit=limit)
        return prices
    except Exception as e:
        logger.error(f"Error getting latest crypto prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/crypto/{symbol}/history", tags=["Cryptocurrency Prices"])
async def get_crypto_history(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168)
):
    """
    Get price history for a cryptocurrency

    **Path Parameters:**
    - **symbol**: Cryptocurrency symbol (e.g., BTC, ETH)

    **Query Parameters:**
    - **hours**: Number of hours of history to retrieve (1-168, default: 24)

    **Returns:**
    - Historical price data with timestamps
    """
    if not pg_reader:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        history = pg_reader.get_crypto_price_history(symbol, hours=hours)
        return {
            "symbol": symbol.upper(),
            "hours": hours,
            "data_points": len(history),
            "history": history
        }
    except Exception as e:
        logger.error(f"Error getting crypto history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================
# NEWS ENDPOINTS
# =====================================

@app.get("/api/news/latest", tags=["News"])
async def get_latest_news(
    limit: int = Query(default=20, ge=1, le=100),
    hours: int = Query(default=24, ge=1, le=168)
):
    """
    Get latest cryptocurrency news

    **Query Parameters:**
    - **limit**: Maximum number of news articles (1-100, default: 20)
    - **hours**: Get news from last N hours (1-168, default: 24)

    **Returns:**
    - List of news articles with title, source, sentiment, and mentioned coins
    """
    if not pg_reader:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        news = pg_reader.get_latest_crypto_news(limit=limit, hours=hours)
        return {
            "count": len(news),
            "hours": hours,
            "news": news
        }
    except Exception as e:
        logger.error(f"Error getting latest news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================
# SOCIAL POSTS ENDPOINTS
# =====================================

@app.get("/api/social/latest", tags=["Social Media"])
async def get_latest_social(
    limit: int = Query(default=20, ge=1, le=100),
    platform: Optional[str] = Query(default=None)
):
    """
    Get latest social media posts

    **Query Parameters:**
    - **limit**: Maximum number of posts (1-100, default: 20)
    - **platform**: Filter by platform (reddit, twitter, telegram) - optional

    **Returns:**
    - List of social media posts with content, sentiment, and engagement metrics
    """
    if not pg_reader:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        posts = pg_reader.get_latest_social_posts(limit=limit, platform=platform)
        return {
            "count": len(posts),
            "platform": platform or "all",
            "posts": posts
        }
    except Exception as e:
        logger.error(f"Error getting social posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================
# ANALYTICS ENDPOINTS
# =====================================

@app.get("/api/analytics/results", tags=["Analytics"])
async def get_analytics_results(
    symbol: Optional[str] = Query(default=None),
    metric_type: Optional[str] = Query(default=None),
    hours: int = Query(default=24, ge=1, le=168)
):
    """
    Get analytics results

    **Query Parameters:**
    - **symbol**: Filter by cryptocurrency symbol (optional)
    - **metric_type**: Filter by metric type (e.g., volatility, correlation) - optional
    - **hours**: Get results from last N hours (1-168, default: 24)

    **Returns:**
    - List of analytics results with computed metrics
    """
    if not pg_reader:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        results = pg_reader.get_analytics_results(
            symbol=symbol,
            metric_type=metric_type,
            hours=hours
        )
        return {
            "count": len(results),
            "symbol": symbol,
            "metric_type": metric_type,
            "hours": hours,
            "results": results
        }
    except Exception as e:
        logger.error(f"Error getting analytics results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/sentiment", tags=["Analytics"])
async def get_sentiment_summary(
    symbol: Optional[str] = Query(default=None),
    time_window: str = Query(default="24h")
):
    """
    Get sentiment analysis summary

    **Query Parameters:**
    - **symbol**: Filter by cryptocurrency symbol (optional)
    - **time_window**: Time window for aggregation (24h, 7d, 30d) - default: 24h

    **Returns:**
    - Aggregated sentiment data with positive/negative/neutral counts
    """
    if not pg_reader:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        sentiment = pg_reader.get_sentiment_summary(
            symbol=symbol,
            time_window=time_window
        )
        return {
            "count": len(sentiment),
            "symbol": symbol,
            "time_window": time_window,
            "sentiment": sentiment
        }
    except Exception as e:
        logger.error(f"Error getting sentiment summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/sentiment/daily", tags=["Analytics"])
async def get_daily_sentiment(
    days: int = Query(default=7, ge=1, le=30)
):
    """
    Get daily sentiment aggregation

    **Query Parameters:**
    - **days**: Number of days of history (1-30, default: 7)

    **Returns:**
    - Daily sentiment trends over time
    """
    if not pg_reader:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        sentiment = pg_reader.get_daily_sentiment(days=days)
        return {
            "count": len(sentiment),
            "days": days,
            "sentiment": sentiment
        }
    except Exception as e:
        logger.error(f"Error getting daily sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/anomalies", tags=["Analytics"])
async def get_active_anomalies(
    symbol: Optional[str] = Query(default=None)
):
    """
    Get active anomalies

    Detects unusual patterns in price, volume, or sentiment data.

    **Query Parameters:**
    - **symbol**: Filter by cryptocurrency symbol (optional)

    **Returns:**
    - List of detected anomalies with severity and description
    """
    if not pg_reader:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        anomalies = pg_reader.get_active_anomalies(symbol=symbol)
        return {
            "count": len(anomalies),
            "symbol": symbol,
            "anomalies": anomalies
        }
    except Exception as e:
        logger.error(f"Error getting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================
# ML PREDICTIONS ENDPOINTS
# =====================================

@app.get("/api/ml/predictions/{symbol}", tags=["Machine Learning"])
async def get_ml_predictions(
    symbol: str,
    prediction_type: Optional[str] = Query(default=None)
):
    """
    Get ML predictions for a cryptocurrency

    **Path Parameters:**
    - **symbol**: Cryptocurrency symbol (e.g., BTC, ETH)

    **Query Parameters:**
    - **prediction_type**: Type of prediction (price, volatility, trend) - optional

    **Returns:**
    - Machine learning predictions with confidence scores
    """
    if not pg_reader:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        predictions = pg_reader.get_ml_predictions(
            symbol=symbol,
            prediction_type=prediction_type
        )
        return {
            "symbol": symbol.upper(),
            "prediction_type": prediction_type,
            "count": len(predictions),
            "predictions": predictions
        }
    except Exception as e:
        logger.error(f"Error getting ML predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower()
    )
