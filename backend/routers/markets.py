"""
CRYPTO VIZ - Markets Router
REST API endpoints for market overview and statistics
"""

import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/markets", tags=["Markets"])

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


@router.get("/overview", summary="Get comprehensive market overview")
async def get_market_overview() -> Dict[str, Any]:
    """
    Get comprehensive cryptocurrency market overview

    Returns:
    - Market statistics (total market cap, volume)
    - Top gainers and losers (24h)
    - Top cryptocurrencies by volume
    - Top cryptocurrencies by market cap
    - Overall market sentiment

    This endpoint provides a complete snapshot of the cryptocurrency market
    """
    try:
        analytics_service = get_analytics_service()
        result = analytics_service.get_market_overview()

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve market overview: {str(e)}")


@router.get("/stats", summary="Get market statistics")
async def get_market_stats():
    """
    Get current market statistics

    Returns key market metrics including:
    - Total market capitalization
    - 24h trading volume
    - Number of tracked cryptocurrencies
    - Market dominance breakdown
    """
    try:
        analytics_service = get_analytics_service()
        overview = analytics_service.get_market_overview()

        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])

        # Extract just the market stats
        return overview.get("market_stats", {})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve market statistics: {str(e)}")


@router.get("/movers", summary="Get top gainers and losers")
async def get_top_movers(
    limit: int = 10
):
    """
    Get top gaining and losing cryptocurrencies (24h)

    - **limit**: Number of movers in each category

    Returns top gainers and losers by 24h price change percentage
    """
    try:
        analytics_service = get_analytics_service()
        overview = analytics_service.get_market_overview()

        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])

        return {
            "top_gainers": overview.get("top_gainers", [])[:limit],
            "top_losers": overview.get("top_losers", [])[:limit]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting top movers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve top movers: {str(e)}")


@router.get("/volume", summary="Get cryptocurrencies by trading volume")
async def get_by_volume(
    limit: int = 20
):
    """
    Get cryptocurrencies sorted by 24h trading volume

    - **limit**: Number of results to return

    Returns top cryptocurrencies by 24h trading volume
    """
    try:
        analytics_service = get_analytics_service()
        overview = analytics_service.get_market_overview()

        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])

        return {
            "top_by_volume": overview.get("top_by_volume", [])[:limit]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting volume leaders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve volume data: {str(e)}")


@router.get("/marketcap", summary="Get cryptocurrencies by market cap")
async def get_by_market_cap(
    limit: int = 20
):
    """
    Get cryptocurrencies sorted by market capitalization

    - **limit**: Number of results to return

    Returns top cryptocurrencies by market cap
    """
    try:
        analytics_service = get_analytics_service()
        overview = analytics_service.get_market_overview()

        if "error" in overview:
            raise HTTPException(status_code=500, detail=overview["error"])

        return {
            "top_by_market_cap": overview.get("top_by_market_cap", [])[:limit]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market cap leaders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve market cap data: {str(e)}")
