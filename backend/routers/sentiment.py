"""
CRYPTO VIZ - Sentiment Router
REST API endpoints for sentiment analysis
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from models.crypto_models import SentimentSummary, SocialPost, ErrorResponse
from services.cache_service import get_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sentiment", tags=["Sentiment"])

# Global reader - will be set by main.py
_pg_reader = None


def set_pg_reader(pg_reader):
    """Set the PostgreSQL reader instance"""
    global _pg_reader
    _pg_reader = pg_reader


def get_pg_reader():
    """Get the PostgreSQL reader instance"""
    if _pg_reader is None:
        raise HTTPException(status_code=500, detail="Database reader not initialized")
    return _pg_reader


@router.get("/{symbol}", summary="Get sentiment analysis for cryptocurrency")
async def get_sentiment_by_symbol(
    symbol: str,
    days: int = Query(default=7, ge=1, le=30, description="Number of days to analyze (1-30)")
):
    """
    Get sentiment analysis for a cryptocurrency

    - **symbol**: Cryptocurrency symbol (e.g., BTC, ETH)
    - **days**: Number of days to analyze (1-30, default: 7)

    Returns aggregated sentiment data from news and social media
    """
    cache = get_cache()
    cache_key = f"{symbol.upper()}:{days}d"

    # Try cache first
    cached = cache.get("sentiment", cache_key)
    if cached:
        logger.info(f"Sentiment cache hit: {symbol}:{days}d")
        return cached

    try:
        pg_reader = get_pg_reader()

        # Get daily sentiment data
        sentiment_data = pg_reader.get_daily_sentiment(days=days)

        # Filter for the requested symbol
        symbol_sentiments = [s for s in sentiment_data if s.get('symbol') == symbol.upper()]

        if not symbol_sentiments:
            raise HTTPException(
                status_code=404,
                detail=f"No sentiment data found for '{symbol}'"
            )

        # Calculate aggregated sentiment
        total_positive = sum(s.get('positive_count', 0) for s in symbol_sentiments)
        total_negative = sum(s.get('negative_count', 0) for s in symbol_sentiments)
        total_neutral = sum(s.get('neutral_count', 0) for s in symbol_sentiments)
        total_count = total_positive + total_negative + total_neutral

        avg_score = sum(s.get('avg_sentiment_score', 0) for s in symbol_sentiments) / len(symbol_sentiments) if symbol_sentiments else 0

        # Determine overall label
        if avg_score > 0.1:
            sentiment_label = "positive"
        elif avg_score < -0.1:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"

        result = {
            "symbol": symbol.upper(),
            "time_window": f"{days}d",
            "sentiment_score": round(avg_score, 3),
            "sentiment_label": sentiment_label,
            "positive_count": total_positive,
            "negative_count": total_negative,
            "neutral_count": total_neutral,
            "total_count": total_count,
            "positive_percent": round(total_positive / total_count * 100, 2) if total_count > 0 else 0,
            "negative_percent": round(total_negative / total_count * 100, 2) if total_count > 0 else 0,
            "neutral_percent": round(total_neutral / total_count * 100, 2) if total_count > 0 else 0,
            "daily_breakdown": symbol_sentiments,
            "calculated_at": datetime.utcnow().isoformat()
        }

        # Cache for 5 minutes
        cache.set("sentiment", cache_key, result, ttl=300)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sentiment for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve sentiment: {str(e)}")


@router.get("/{symbol}/social", response_model=List[SocialPost], summary="Get social media posts")
async def get_social_posts(
    symbol: str,
    limit: int = Query(default=20, ge=1, le=100, description="Number of posts to return"),
    platform: Optional[str] = Query(default=None, description="Platform filter: reddit, twitter")
):
    """
    Get recent social media posts mentioning a cryptocurrency

    - **symbol**: Cryptocurrency symbol
    - **limit**: Number of posts (1-100, default: 20)
    - **platform**: Filter by platform (reddit, twitter)

    Returns list of social media posts with sentiment scores
    """
    cache = get_cache()
    cache_key = f"{symbol.upper()}:{limit}:{platform or 'all'}"

    # Try cache first
    cached = cache.get("social_posts", cache_key)
    if cached:
        return cached

    try:
        pg_reader = get_pg_reader()
        posts = pg_reader.get_latest_social_posts(limit=limit * 2, platform=platform)  # Get more to filter

        # Filter posts that mention the symbol
        symbol_upper = symbol.upper()
        filtered_posts = [
            p for p in posts
            if p.get('mentioned_coins') and symbol_upper in [c.upper() for c in p.get('mentioned_coins', [])]
        ][:limit]

        if not filtered_posts:
            raise HTTPException(
                status_code=404,
                detail=f"No social posts found mentioning '{symbol}'"
            )

        # Cache for 2 minutes
        cache.set("social_posts", cache_key, filtered_posts, ttl=120)

        return filtered_posts

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting social posts for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve social posts: {str(e)}")


@router.get("/overall/summary", summary="Get overall market sentiment")
async def get_overall_sentiment(
    time_window: str = Query(default="24h", description="Time window: 1h, 4h, 12h, 24h, 7d")
):
    """
    Get overall cryptocurrency market sentiment

    - **time_window**: Time window (1h, 4h, 12h, 24h, 7d)

    Returns aggregated sentiment across all tracked cryptocurrencies
    """
    cache = get_cache()
    cache_key = time_window

    # Try cache first
    cached = cache.get("overall_sentiment", cache_key)
    if cached:
        return cached

    try:
        pg_reader = get_pg_reader()
        sentiment_data = pg_reader.get_sentiment_summary(symbol=None, time_window=time_window)

        if not sentiment_data:
            raise HTTPException(
                status_code=404,
                detail=f"No sentiment data available for {time_window}"
            )

        # Calculate overall statistics
        total_positive = sum(s.get('positive_count', 0) for s in sentiment_data)
        total_negative = sum(s.get('negative_count', 0) for s in sentiment_data)
        total_neutral = sum(s.get('neutral_count', 0) for s in sentiment_data)
        total_count = total_positive + total_negative + total_neutral

        avg_score = sum(s.get('sentiment_score', 0) * s.get('total_count', 0) for s in sentiment_data) / total_count if total_count > 0 else 0

        # Determine overall label
        if avg_score > 0.1:
            sentiment_label = "positive"
        elif avg_score < -0.1:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"

        result = {
            "time_window": time_window,
            "sentiment_score": round(avg_score, 3),
            "sentiment_label": sentiment_label,
            "positive_count": total_positive,
            "negative_count": total_negative,
            "neutral_count": total_neutral,
            "total_count": total_count,
            "positive_percent": round(total_positive / total_count * 100, 2) if total_count > 0 else 0,
            "negative_percent": round(total_negative / total_count * 100, 2) if total_count > 0 else 0,
            "neutral_percent": round(total_neutral / total_count * 100, 2) if total_count > 0 else 0,
            "by_symbol": sentiment_data,
            "calculated_at": datetime.utcnow().isoformat()
        }

        # Cache for 2 minutes
        cache.set("overall_sentiment", cache_key, result, ttl=120)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting overall sentiment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve overall sentiment: {str(e)}")
