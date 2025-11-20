"""
CRYPTO VIZ - News Router
REST API endpoints for cryptocurrency news
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from models.crypto_models import CryptoNews, ErrorResponse
from services.cache_service import get_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/news", tags=["News"])

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


@router.get("", response_model=List[CryptoNews], summary="Get latest cryptocurrency news")
async def get_all_news(
    limit: int = Query(default=20, ge=1, le=100, description="Number of articles to return"),
    page: int = Query(default=1, ge=1, description="Page number for pagination"),
    hours: int = Query(default=24, ge=1, le=720, description="Time window in hours")
):
    """
    Get latest cryptocurrency news articles

    - **limit**: Number of articles per page (1-100, default: 20)
    - **page**: Page number (starts at 1)
    - **hours**: Time window in hours (1-720, default: 24)

    Returns paginated list of news articles with sentiment analysis
    """
    cache = get_cache()
    cache_key = f"all:{limit}:{page}:{hours}"

    # Try cache first
    cached = cache.get("news", cache_key)
    if cached:
        logger.info(f"News cache hit: limit={limit}, page={page}, hours={hours}")
        return cached

    try:
        pg_reader = get_pg_reader()

        # Get news (fetch more than needed for pagination)
        total_limit = limit * page
        news = pg_reader.get_latest_crypto_news(limit=total_limit, hours=hours)

        if not news:
            return []

        # Paginate results
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_news = news[start_idx:end_idx]

        # Cache for 2 minutes
        cache.set("news", cache_key, paginated_news, ttl=120)

        return paginated_news

    except Exception as e:
        logger.error(f"Error getting all news: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve news: {str(e)}")


@router.get("/{symbol}", response_model=List[CryptoNews], summary="Get news for specific cryptocurrency")
async def get_news_by_symbol(
    symbol: str,
    limit: int = Query(default=20, ge=1, le=100, description="Number of articles to return"),
    page: int = Query(default=1, ge=1, description="Page number for pagination"),
    hours: int = Query(default=168, ge=1, le=720, description="Time window in hours (default: 7 days)")
):
    """
    Get news articles mentioning a specific cryptocurrency

    - **symbol**: Cryptocurrency symbol (e.g., BTC, ETH)
    - **limit**: Number of articles per page (1-100, default: 20)
    - **page**: Page number (starts at 1)
    - **hours**: Time window in hours (1-720, default: 168 = 7 days)

    Returns news articles that mention the specified cryptocurrency
    """
    cache = get_cache()
    cache_key = f"{symbol.upper()}:{limit}:{page}:{hours}"

    # Try cache first
    cached = cache.get("news", cache_key)
    if cached:
        logger.info(f"News cache hit: {symbol}:{limit}:{page}:{hours}")
        return cached

    try:
        pg_reader = get_pg_reader()

        # Get more news to filter
        all_news = pg_reader.get_latest_crypto_news(limit=500, hours=hours)

        # Filter news that mention the symbol
        symbol_upper = symbol.upper()
        filtered_news = [
            n for n in all_news
            if n.get('mentioned_coins') and symbol_upper in [c.upper() for c in n.get('mentioned_coins', [])]
        ]

        if not filtered_news:
            raise HTTPException(
                status_code=404,
                detail=f"No news found mentioning '{symbol}'"
            )

        # Paginate results
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_news = filtered_news[start_idx:end_idx]

        # Cache for 2 minutes
        cache.set("news", cache_key, paginated_news, ttl=120)

        return paginated_news

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting news for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve news: {str(e)}")


@router.get("/{symbol}/stats", summary="Get news statistics for cryptocurrency")
async def get_news_stats(
    symbol: str,
    hours: int = Query(default=168, ge=1, le=720, description="Time window in hours")
):
    """
    Get statistics about news coverage for a cryptocurrency

    - **symbol**: Cryptocurrency symbol
    - **hours**: Time window in hours (default: 168 = 7 days)

    Returns statistics: article count, sentiment breakdown, source distribution
    """
    cache = get_cache()
    cache_key = f"{symbol.upper()}:stats:{hours}"

    # Try cache first
    cached = cache.get("news_stats", cache_key)
    if cached:
        return cached

    try:
        pg_reader = get_pg_reader()
        all_news = pg_reader.get_latest_crypto_news(limit=500, hours=hours)

        # Filter news for the symbol
        symbol_upper = symbol.upper()
        symbol_news = [
            n for n in all_news
            if n.get('mentioned_coins') and symbol_upper in [c.upper() for c in n.get('mentioned_coins', [])]
        ]

        if not symbol_news:
            raise HTTPException(
                status_code=404,
                detail=f"No news found for '{symbol}'"
            )

        # Calculate sentiment distribution
        sentiments = [n.get('sentiment_label') for n in symbol_news if n.get('sentiment_label')]
        positive_count = sentiments.count('positive')
        negative_count = sentiments.count('negative')
        neutral_count = sentiments.count('neutral')
        total_count = len(sentiments)

        # Calculate average sentiment score
        sentiment_scores = [n.get('sentiment_score') for n in symbol_news if n.get('sentiment_score') is not None]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

        # Get source distribution
        sources = [n.get('source') for n in symbol_news if n.get('source')]
        source_counts = {}
        for source in sources:
            source_counts[source] = source_counts.get(source, 0) + 1

        # Sort sources by count
        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        result = {
            "symbol": symbol_upper,
            "time_window": f"{hours}h",
            "total_articles": len(symbol_news),
            "sentiment": {
                "average_score": round(avg_sentiment, 3),
                "positive_count": positive_count,
                "negative_count": negative_count,
                "neutral_count": neutral_count,
                "positive_percent": round(positive_count / total_count * 100, 2) if total_count > 0 else 0,
                "negative_percent": round(negative_count / total_count * 100, 2) if total_count > 0 else 0,
                "neutral_percent": round(neutral_count / total_count * 100, 2) if total_count > 0 else 0
            },
            "sources": {
                "total_sources": len(source_counts),
                "top_sources": [{"source": source, "count": count} for source, count in top_sources]
            },
            "calculated_at": datetime.utcnow().isoformat()
        }

        # Cache for 5 minutes
        cache.set("news_stats", cache_key, result, ttl=300)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating news stats for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate news statistics: {str(e)}")


@router.get("/sentiment/breakdown", summary="Get news sentiment breakdown")
async def get_sentiment_breakdown(
    hours: int = Query(default=24, ge=1, le=720, description="Time window in hours")
):
    """
    Get overall news sentiment breakdown across all cryptocurrencies

    - **hours**: Time window in hours (default: 24)

    Returns sentiment distribution and top mentioned cryptocurrencies
    """
    cache = get_cache()
    cache_key = f"breakdown:{hours}"

    # Try cache first
    cached = cache.get("news_sentiment", cache_key)
    if cached:
        return cached

    try:
        pg_reader = get_pg_reader()
        all_news = pg_reader.get_latest_crypto_news(limit=500, hours=hours)

        if not all_news:
            return {
                "error": "No news data available"
            }

        # Calculate overall sentiment
        sentiments = [n.get('sentiment_label') for n in all_news if n.get('sentiment_label')]
        positive_count = sentiments.count('positive')
        negative_count = sentiments.count('negative')
        neutral_count = sentiments.count('neutral')
        total_count = len(sentiments)

        # Get most mentioned coins
        coin_mentions = {}
        for article in all_news:
            if article.get('mentioned_coins'):
                for coin in article['mentioned_coins']:
                    coin_mentions[coin] = coin_mentions.get(coin, 0) + 1

        top_mentioned = sorted(coin_mentions.items(), key=lambda x: x[1], reverse=True)[:20]

        result = {
            "time_window": f"{hours}h",
            "total_articles": len(all_news),
            "sentiment": {
                "positive_count": positive_count,
                "negative_count": negative_count,
                "neutral_count": neutral_count,
                "positive_percent": round(positive_count / total_count * 100, 2) if total_count > 0 else 0,
                "negative_percent": round(negative_count / total_count * 100, 2) if total_count > 0 else 0,
                "neutral_percent": round(neutral_count / total_count * 100, 2) if total_count > 0 else 0
            },
            "top_mentioned": [{"symbol": coin, "mentions": count} for coin, count in top_mentioned],
            "calculated_at": datetime.utcnow().isoformat()
        }

        # Cache for 2 minutes
        cache.set("news_sentiment", cache_key, result, ttl=120)

        return result

    except Exception as e:
        logger.error(f"Error getting sentiment breakdown: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate sentiment breakdown: {str(e)}")
