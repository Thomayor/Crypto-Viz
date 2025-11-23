"""
CRYPTO VIZ - Prices Router
REST API endpoints for cryptocurrency prices
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from models.crypto_models import CryptoPrice, CryptoPriceHistory, ErrorResponse
from services.cache_service import get_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/prices", tags=["Prices"])

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


@router.get("", response_model=List[CryptoPrice], summary="Get all cryptocurrency prices")
async def get_all_prices(
    limit: int = Query(default=50, ge=1, le=200, description="Number of cryptocurrencies to return"),
    sort_by: str = Query(default="market_cap", description="Sort by: market_cap, volume_24h, rank"),
    order: str = Query(default="desc", description="Sort order: asc, desc")
):
    """
    Get list of all cryptocurrency prices

    - **limit**: Number of results (1-200, default: 50)
    - **sort_by**: Sort field (market_cap, volume_24h, rank)
    - **order**: Sort order (asc, desc)

    Returns list of cryptocurrency prices with current market data
    """
    cache = get_cache()
    cache_key = f"all:{limit}:{sort_by}:{order}"

    # Try cache first
    cached = cache.get("prices", cache_key)
    if cached:
        logger.info(f"Prices cache hit: {cache_key}")
        return cached

    try:
        pg_reader = get_pg_reader()
        prices = pg_reader.get_latest_crypto_prices(limit=limit)

        if not prices:
            return []

        # Sort results
        sort_key_map = {
            "market_cap": lambda x: x.get('market_cap') or 0,
            "volume_24h": lambda x: x.get('volume_24h') or 0,
            "rank": lambda x: x.get('rank') or 999999
        }

        sort_key = sort_key_map.get(sort_by, sort_key_map["market_cap"])
        reverse = (order.lower() == "desc")

        sorted_prices = sorted(prices, key=sort_key, reverse=reverse)

        # Cache for 30 seconds
        cache.set("prices", cache_key, sorted_prices, ttl=30)

        return sorted_prices

    except Exception as e:
        logger.error(f"Error getting all prices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve prices: {str(e)}")


@router.get("/rsi/daily-prices", summary="Get daily closing prices for RSI calculation")
async def get_daily_prices_for_rsi(
    days: int = Query(default=14, ge=2, le=30, description="Number of days (2-30, default: 14)")
):
    """
    Get daily closing prices for all tracked cryptocurrencies for RSI calculation

    - **days**: Number of days to fetch (2-30, default: 14)

    Returns daily closing prices grouped by symbol for proper RSI calculation
    """
    cache = get_cache()
    cache_key = f"rsi_daily:{days}"

    # Try cache first (cache for 5 minutes since this is for dashboard)
    cached = cache.get("rsi_daily", cache_key)
    if cached:
        logger.info(f"RSI daily prices cache hit: {days} days")
        return cached

    try:
        pg_reader = get_pg_reader()

        # Get daily closing prices for the last N days
        # We'll query the database for daily aggregated data
        hours = days * 24

        # Get latest prices to know which symbols to track
        latest_prices = pg_reader.get_latest_crypto_prices(limit=50)

        result = {}

        for coin in latest_prices:
            symbol = coin['symbol']

            # Get hourly history and group by day
            history = pg_reader.get_crypto_price_history(symbol, hours=hours)

            if not history:
                continue

            # Group by day and get the last price of each day
            daily_prices = {}
            for record in history:
                timestamp = record.get('timestamp')
                price = record.get('price')

                if timestamp and price:
                    # Extract date (YYYY-MM-DD)
                    if isinstance(timestamp, str):
                        date = timestamp.split('T')[0]
                    else:
                        date = timestamp.strftime('%Y-%m-%d')

                    # Keep the latest price for each day
                    if date not in daily_prices or timestamp > daily_prices[date]['timestamp']:
                        daily_prices[date] = {
                            'date': date,
                            'price': float(price),
                            'timestamp': timestamp
                        }

            # Sort by date and extract just the prices
            sorted_days = sorted(daily_prices.keys())
            daily_closing_prices = [daily_prices[day]['price'] for day in sorted_days]

            if daily_closing_prices:
                result[symbol] = {
                    'symbol': symbol,
                    'daily_prices': daily_closing_prices,
                    'days_available': len(daily_closing_prices),
                    'oldest_date': sorted_days[0] if sorted_days else None,
                    'newest_date': sorted_days[-1] if sorted_days else None
                }

        response = {
            'requested_days': days,
            'coins': result,
            'total_coins': len(result)
        }

        # Cache for 5 minutes
        cache.set("rsi_daily", cache_key, response, ttl=300)

        return response

    except Exception as e:
        logger.error(f"Error getting daily prices for RSI: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve daily prices: {str(e)}")


@router.get("/{symbol}", response_model=CryptoPrice, summary="Get specific cryptocurrency price")
async def get_price_by_symbol(
    symbol: str
):
    """
    Get current price data for a specific cryptocurrency

    - **symbol**: Cryptocurrency symbol (e.g., BTC, ETH, SOL)

    Returns current price, market cap, volume, and other market data
    """
    cache = get_cache()
    cache_key = symbol.upper()

    # Try cache first
    cached = cache.get("price", cache_key)
    if cached:
        logger.info(f"Price cache hit: {symbol}")
        return cached

    try:
        pg_reader = get_pg_reader()
        prices = pg_reader.get_latest_crypto_prices(limit=200)

        # Find the requested symbol
        crypto = next((p for p in prices if p['symbol'] == symbol.upper()), None)

        if not crypto:
            raise HTTPException(
                status_code=404,
                detail=f"Cryptocurrency '{symbol}' not found"
            )

        # Cache for 30 seconds
        cache.set("price", cache_key, crypto, ttl=30)

        return crypto

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve price: {str(e)}")


@router.get("/{symbol}/history", response_model=CryptoPriceHistory, summary="Get price history")
async def get_price_history(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=720, description="Hours of history (1-720, default: 24)")
):
    """
    Get historical price data for a cryptocurrency

    - **symbol**: Cryptocurrency symbol
    - **hours**: Number of hours of history (1-720, default: 24)

    Returns time series of price data with timestamps
    """
    cache = get_cache()
    cache_key = f"{symbol.upper()}:history:{hours}"

    # Try cache first
    cached = cache.get("price_history", cache_key)
    if cached:
        logger.info(f"Price history cache hit: {symbol}:{hours}h")
        return cached

    try:
        pg_reader = get_pg_reader()
        history = pg_reader.get_crypto_price_history(symbol, hours=hours)

        if not history:
            raise HTTPException(
                status_code=404,
                detail=f"No history found for '{symbol}'"
            )

        result = {
            "symbol": symbol.upper(),
            "hours": hours,
            "data_points": len(history),
            "history": history
        }

        # Cache for 1 minute
        cache.set("price_history", cache_key, result, ttl=60)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting price history for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve price history: {str(e)}")


@router.get("/{symbol}/stats", summary="Get price statistics")
async def get_price_stats(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=720, description="Time window for stats")
):
    """
    Get statistical analysis of price data

    - **symbol**: Cryptocurrency symbol
    - **hours**: Time window in hours

    Returns min, max, avg, volatility, and other statistics
    """
    cache = get_cache()
    cache_key = f"{symbol.upper()}:stats:{hours}"

    # Try cache first
    cached = cache.get("price_stats", cache_key)
    if cached:
        return cached

    try:
        pg_reader = get_pg_reader()
        history = pg_reader.get_crypto_price_history(symbol, hours=hours)

        if not history:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for '{symbol}'"
            )

        prices = [float(p['price']) for p in history if p.get('price')]

        if not prices:
            raise HTTPException(
                status_code=404,
                detail=f"No valid price data for '{symbol}'"
            )

        # Calculate statistics
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        price_change = prices[-1] - prices[0] if len(prices) > 1 else 0
        price_change_percent = (price_change / prices[0] * 100) if prices[0] != 0 else 0

        # Calculate volatility (standard deviation)
        variance = sum((p - avg_price) ** 2 for p in prices) / len(prices)
        volatility = variance ** 0.5

        result = {
            "symbol": symbol.upper(),
            "time_window": f"{hours}h",
            "data_points": len(prices),
            "current_price": prices[-1],
            "min_price": min_price,
            "max_price": max_price,
            "avg_price": avg_price,
            "price_change": price_change,
            "price_change_percent": price_change_percent,
            "volatility": volatility,
            "volatility_percent": (volatility / avg_price * 100) if avg_price != 0 else 0,
            "calculated_at": datetime.utcnow().isoformat()
        }

        # Cache for 1 minute
        cache.set("price_stats", cache_key, result, ttl=60)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating stats for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate statistics: {str(e)}")
