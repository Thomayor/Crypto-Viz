"""
CRYPTO VIZ - Crypto Data Models
Pydantic models for cryptocurrency data validation and serialization
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# =====================================
# ENUMS
# =====================================

class SentimentLabel(str, Enum):
    """Sentiment classification labels"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class PredictionType(str, Enum):
    """ML prediction types"""
    PRICE = "price"
    VOLATILITY = "volatility"
    TREND = "trend"


class Platform(str, Enum):
    """Social media platforms"""
    REDDIT = "reddit"
    TWITTER = "twitter"
    TELEGRAM = "telegram"


# =====================================
# CRYPTO PRICES
# =====================================

class CryptoPrice(BaseModel):
    """Cryptocurrency price data"""
    symbol: str = Field(..., description="Cryptocurrency symbol (e.g., BTC, ETH)")
    name: Optional[str] = Field(None, description="Cryptocurrency name")
    price: float = Field(..., description="Current price in USD")
    price_change_24h: Optional[float] = Field(None, description="24h price change percentage")
    volume_24h: Optional[float] = Field(None, description="24h trading volume")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    rank: Optional[int] = Field(None, description="Market cap rank")
    timestamp: datetime = Field(..., description="Data timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC",
                "name": "Bitcoin",
                "price": 45000.0,
                "price_change_24h": 2.5,
                "volume_24h": 1200000000.0,
                "market_cap": 850000000000.0,
                "rank": 1,
                "timestamp": "2024-11-12T15:30:00Z"
            }
        }


class CryptoPriceHistory(BaseModel):
    """Historical price data for a cryptocurrency"""
    symbol: str = Field(..., description="Cryptocurrency symbol")
    hours: int = Field(..., description="Number of hours of history")
    data_points: int = Field(..., description="Number of data points")
    history: List[Dict[str, Any]] = Field(..., description="Historical price data")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC",
                "hours": 24,
                "data_points": 144,
                "history": [
                    {"timestamp": "2024-11-12T15:00:00Z", "price": 45000.0, "volume": 1000000.0}
                ]
            }
        }


# =====================================
# NEWS & SOCIAL
# =====================================

class CryptoNews(BaseModel):
    """Cryptocurrency news article"""
    title: str = Field(..., description="Article title")
    description: Optional[str] = Field(None, description="Article description")
    url: str = Field(..., description="Article URL")
    source: str = Field(..., description="News source")
    published_at: datetime = Field(..., description="Publication timestamp")
    sentiment_score: Optional[float] = Field(None, description="Sentiment score (-1 to 1)")
    sentiment_label: Optional[SentimentLabel] = Field(None, description="Sentiment classification")
    analysis_method: Optional[str] = Field(None, description="Sentiment analysis method (ollama or lexicon)")
    confidence_score: Optional[float] = Field(None, description="Sentiment confidence score (0-1)")
    keywords: Optional[List[str]] = Field(None, description="Keywords extracted from sentiment analysis")
    mentioned_coins: Optional[List[str]] = Field(None, description="Mentioned cryptocurrencies")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Bitcoin reaches new all-time high",
                "description": "Bitcoin surpassed $50,000 for the first time...",
                "url": "https://example.com/bitcoin-ath",
                "source": "CoinDesk",
                "published_at": "2024-11-12T15:00:00Z",
                "sentiment_score": 0.85,
                "sentiment_label": "positive",
                "analysis_method": "ollama",
                "confidence_score": 0.92,
                "keywords": ["bitcoin", "all-time high"],
                "mentioned_coins": ["BTC", "ETH"]
            }
        }


class SocialPost(BaseModel):
    """Social media post about cryptocurrency"""
    platform: Platform = Field(..., description="Social media platform")
    post_id: str = Field(..., description="Post identifier")
    author: str = Field(..., description="Post author")
    content: str = Field(..., description="Post content")
    created_at: datetime = Field(..., description="Creation timestamp")
    engagement: Optional[Dict[str, int]] = Field(None, description="Engagement metrics (likes, shares, etc.)")
    sentiment_score: Optional[float] = Field(None, description="Sentiment score")
    mentioned_coins: Optional[List[str]] = Field(None, description="Mentioned cryptocurrencies")

    class Config:
        json_schema_extra = {
            "example": {
                "platform": "reddit",
                "post_id": "abc123",
                "author": "crypto_enthusiast",
                "content": "Bitcoin looking bullish! 🚀",
                "created_at": "2024-11-12T15:00:00Z",
                "engagement": {"upvotes": 150, "comments": 25},
                "sentiment_score": 0.75,
                "mentioned_coins": ["BTC"]
            }
        }


# =====================================
# ANALYTICS & ML
# =====================================

class AnalyticsResult(BaseModel):
    """Analytics computation result"""
    symbol: str = Field(..., description="Cryptocurrency symbol")
    metric_type: str = Field(..., description="Type of metric (e.g., volatility, correlation)")
    metric_value: float = Field(..., description="Computed metric value")
    calculated_at: datetime = Field(..., description="Calculation timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC",
                "metric_type": "volatility",
                "metric_value": 0.035,
                "calculated_at": "2024-11-12T15:00:00Z",
                "metadata": {"window": "24h", "method": "std_dev"}
            }
        }


class SentimentSummary(BaseModel):
    """Aggregated sentiment analysis"""
    symbol: Optional[str] = Field(None, description="Cryptocurrency symbol (null for overall)")
    time_window: str = Field(..., description="Time window (e.g., 24h, 7d)")
    sentiment_score: float = Field(..., description="Average sentiment score")
    sentiment_label: SentimentLabel = Field(..., description="Overall sentiment classification")
    positive_count: int = Field(..., description="Number of positive mentions")
    negative_count: int = Field(..., description="Number of negative mentions")
    neutral_count: int = Field(..., description="Number of neutral mentions")
    total_count: int = Field(..., description="Total number of mentions")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC",
                "time_window": "24h",
                "sentiment_score": 0.42,
                "sentiment_label": "positive",
                "positive_count": 120,
                "negative_count": 30,
                "neutral_count": 50,
                "total_count": 200
            }
        }


class MLPrediction(BaseModel):
    """Machine learning prediction"""
    symbol: str = Field(..., description="Cryptocurrency symbol")
    prediction_type: PredictionType = Field(..., description="Type of prediction")
    predicted_value: float = Field(..., description="Predicted value")
    confidence: Optional[float] = Field(None, description="Prediction confidence (0-1)")
    prediction_time: datetime = Field(..., description="When prediction was made")
    target_time: datetime = Field(..., description="Target time for prediction")
    model_version: Optional[str] = Field(None, description="ML model version")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC",
                "prediction_type": "price",
                "predicted_value": 46500.0,
                "confidence": 0.85,
                "prediction_time": "2024-11-12T15:00:00Z",
                "target_time": "2024-11-12T16:00:00Z",
                "model_version": "v1.2.0"
            }
        }


class Anomaly(BaseModel):
    """Detected anomaly in crypto data"""
    symbol: str = Field(..., description="Cryptocurrency symbol")
    anomaly_type: str = Field(..., description="Type of anomaly (price, volume, sentiment)")
    detected_at: datetime = Field(..., description="Detection timestamp")
    severity: str = Field(..., description="Severity level (low, medium, high)")
    description: str = Field(..., description="Anomaly description")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC",
                "anomaly_type": "price",
                "detected_at": "2024-11-12T15:00:00Z",
                "severity": "high",
                "description": "Unusual price spike detected (+15% in 5 minutes)",
                "metadata": {"price_change": 15.2, "z_score": 4.5}
            }
        }


# =====================================
# SYSTEM & HEALTH
# =====================================

class DatabaseStats(BaseModel):
    """Database statistics"""
    total_prices: int = Field(..., description="Total price records")
    total_news: int = Field(..., description="Total news articles")
    total_social_posts: int = Field(..., description="Total social posts")
    total_analytics: int = Field(..., description="Total analytics results")
    last_update: Optional[datetime] = Field(None, description="Last data update")

    class Config:
        json_schema_extra = {
            "example": {
                "total_prices": 15000,
                "total_news": 500,
                "total_social_posts": 2000,
                "total_analytics": 1000,
                "last_update": "2024-11-12T15:00:00Z"
            }
        }


class HealthCheck(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Overall status (healthy, degraded, unhealthy)")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    database: str = Field(..., description="Database connection status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    db_stats: Optional[DatabaseStats] = Field(None, description="Database statistics")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "crypto-viz-backend",
                "version": "2.0.0",
                "database": "connected",
                "timestamp": "2024-11-12T15:00:00Z",
                "db_stats": {
                    "total_prices": 15000,
                    "total_news": 500,
                    "total_social_posts": 2000,
                    "total_analytics": 1000
                }
            }
        }


# =====================================
# REQUEST/RESPONSE WRAPPERS
# =====================================

class ListResponse(BaseModel):
    """Generic list response wrapper"""
    count: int = Field(..., description="Number of items returned")
    items: List[Any] = Field(..., description="List of items")
    total: Optional[int] = Field(None, description="Total items available")
    page: Optional[int] = Field(None, description="Current page number")
    page_size: Optional[int] = Field(None, description="Items per page")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "Resource not found",
                "detail": "Cryptocurrency symbol 'XYZ' not found in database",
                "timestamp": "2024-11-12T15:00:00Z"
            }
        }
