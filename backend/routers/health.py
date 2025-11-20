"""
CRYPTO VIZ - Health Check Router
Endpoints for service health and status monitoring
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging
from datetime import datetime

from models.crypto_models import HealthCheck, DatabaseStats
from config import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    tags=["Health & Status"],
    responses={
        503: {"description": "Service Unavailable"},
        500: {"description": "Internal Server Error"}
    }
)


# Dependency injection for database reader (will be set in main.py)
_pg_reader = None


def set_pg_reader(pg_reader):
    """Set the PostgreSQL reader instance"""
    global _pg_reader
    _pg_reader = pg_reader


def get_pg_reader():
    """Get the PostgreSQL reader instance"""
    return _pg_reader


@router.get("/", summary="Root endpoint", response_model=dict)
async def root():
    """
    Root endpoint with API information

    Returns basic information about the API including:
    - Service name and version
    - Storage backend type
    - Link to interactive documentation
    """
    return {
        "message": f"{settings.app_name} is running",
        "version": settings.app_version,
        "storage": "PostgreSQL",
        "docs": "/docs",
        "health": "/health"
    }


@router.get("/health", summary="Health check", response_model=HealthCheck)
async def health_check():
    """
    Comprehensive health check endpoint

    Checks:
    - API service status
    - PostgreSQL database connectivity
    - Database statistics (if connected)

    Returns:
    - **status**: Overall health status (healthy, degraded, unhealthy)
    - **service**: Service name
    - **version**: API version
    - **database**: Database connection status
    - **db_stats**: Database statistics (if available)

    Status Codes:
    - **200**: Service is healthy
    - **503**: Service is degraded or unhealthy
    """
    health_status = {
        "status": "healthy",
        "service": "crypto-viz-backend",
        "version": settings.app_version,
        "database": "unknown",
        "timestamp": datetime.utcnow()
    }

    # Check PostgreSQL connection
    pg_reader = get_pg_reader()
    if pg_reader:
        try:
            stats = pg_reader.get_database_stats()
            health_status["database"] = "connected"
            # Map database stats to model fields
            health_status["db_stats"] = DatabaseStats(
                total_prices=stats.get('crypto_prices_count', 0),
                total_news=stats.get('crypto_news_count', 0),
                total_social_posts=stats.get('social_posts_count', 0),
                total_analytics=stats.get('analytics_results_count', 0),
                last_update=stats.get('latest_price_update')
            )
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_status["database"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
    else:
        health_status["database"] = "not initialized"
        health_status["status"] = "degraded"

    return HealthCheck(**health_status)


@router.get("/api/stats", summary="Get database statistics", response_model=DatabaseStats)
async def get_stats():
    """
    Get detailed database statistics

    Returns counts of:
    - Price records
    - News articles
    - Social media posts
    - Analytics results
    - Last update timestamp

    Raises:
    - **503**: Database not initialized
    - **500**: Error retrieving statistics
    """
    pg_reader = get_pg_reader()
    if not pg_reader:
        raise HTTPException(status_code=503, detail="Database not initialized")

    try:
        stats = pg_reader.get_database_stats()
        # Map database stats to model fields
        return DatabaseStats(
            total_prices=stats.get('crypto_prices_count', 0),
            total_news=stats.get('crypto_news_count', 0),
            total_social_posts=stats.get('social_posts_count', 0),
            total_analytics=stats.get('analytics_results_count', 0),
            last_update=stats.get('latest_price_update')
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/info", summary="Get API information")
async def get_api_info():
    """
    Get detailed API configuration information

    Returns:
    - Application name and version
    - Environment settings (non-sensitive)
    - Enabled features
    - CORS configuration
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": settings.app_description,
        "environment": {
            "debug": settings.debug,
            "log_level": settings.log_level
        },
        "features": {
            "rate_limiting": settings.rate_limit_enabled,
            "websockets": False  # Not yet implemented
        },
        "cors": {
            "origins": settings.cors_origins_list,
            "credentials": settings.cors_credentials
        },
        "database": {
            "type": "PostgreSQL",
            "host": settings.postgres_host,
            "port": settings.postgres_port,
            "database": settings.postgres_db
        }
    }
