"""
CRYPTO VIZ - Cache Service
Redis-based caching service for API responses
"""

import os
import json
import logging
from typing import Optional, Any
from datetime import timedelta
import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheService:
    """Redis cache service for API responses"""

    def __init__(self):
        """Initialize Redis connection"""
        self.host = os.getenv('REDIS_HOST', 'redis')
        self.port = int(os.getenv('REDIS_PORT', '6379'))
        self.db = int(os.getenv('REDIS_DB', '0'))
        self.enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'

        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"✓ Redis cache connected: {self.host}:{self.port}")
        except RedisError as e:
            logger.warning(f"Redis connection failed: {e}. Cache disabled.")
            self.enabled = False
            self.redis_client = None

    def _make_key(self, prefix: str, key: str) -> str:
        """Create namespaced cache key"""
        return f"crypto_viz:{prefix}:{key}"

    def get(self, prefix: str, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            prefix: Cache namespace (e.g., 'prices', 'analytics')
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            cache_key = self._make_key(prefix, key)
            value = self.redis_client.get(cache_key)

            if value:
                logger.debug(f"Cache HIT: {cache_key}")
                return json.loads(value)
            else:
                logger.debug(f"Cache MISS: {cache_key}")
                return None

        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Cache get error for {prefix}:{key}: {e}")
            return None

    def set(self, prefix: str, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set value in cache with TTL

        Args:
            prefix: Cache namespace
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time to live in seconds (default: 5 minutes)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            cache_key = self._make_key(prefix, key)
            serialized = json.dumps(value, default=str)  # default=str for datetime
            self.redis_client.setex(cache_key, ttl, serialized)
            logger.debug(f"Cache SET: {cache_key} (TTL: {ttl}s)")
            return True

        except (RedisError, TypeError, ValueError) as e:
            logger.error(f"Cache set error for {prefix}:{key}: {e}")
            return False

    def delete(self, prefix: str, key: str) -> bool:
        """
        Delete key from cache

        Args:
            prefix: Cache namespace
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            cache_key = self._make_key(prefix, key)
            self.redis_client.delete(cache_key)
            logger.debug(f"Cache DELETE: {cache_key}")
            return True

        except RedisError as e:
            logger.error(f"Cache delete error for {prefix}:{key}: {e}")
            return False

    def delete_pattern(self, prefix: str, pattern: str = "*") -> int:
        """
        Delete all keys matching pattern

        Args:
            prefix: Cache namespace
            pattern: Pattern to match (default: all keys in prefix)

        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0

        try:
            cache_pattern = self._make_key(prefix, pattern)
            keys = self.redis_client.keys(cache_pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cache FLUSH: Deleted {deleted} keys matching {cache_pattern}")
                return deleted
            return 0

        except RedisError as e:
            logger.error(f"Cache delete pattern error for {prefix}:{pattern}: {e}")
            return 0

    def flush_all(self) -> bool:
        """
        Flush all crypto_viz cache keys

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            keys = self.redis_client.keys("crypto_viz:*")
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cache FLUSH ALL: Deleted {deleted} keys")
            return True

        except RedisError as e:
            logger.error(f"Cache flush all error: {e}")
            return False

    def get_stats(self) -> dict:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        if not self.enabled or not self.redis_client:
            return {
                "enabled": False,
                "connected": False
            }

        try:
            info = self.redis_client.info()
            keys_count = len(self.redis_client.keys("crypto_viz:*"))

            return {
                "enabled": True,
                "connected": True,
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "keys_count": keys_count,
                "memory_used": info.get('used_memory_human', 'N/A'),
                "connected_clients": info.get('connected_clients', 0),
                "uptime_seconds": info.get('uptime_in_seconds', 0)
            }

        except RedisError as e:
            logger.error(f"Cache stats error: {e}")
            return {
                "enabled": True,
                "connected": False,
                "error": str(e)
            }

    def close(self):
        """Close Redis connection"""
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Redis cache connection closed")
            except RedisError as e:
                logger.error(f"Error closing Redis connection: {e}")


# Global cache instance
_cache_instance: Optional[CacheService] = None


def get_cache() -> CacheService:
    """Get or create global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance


def close_cache():
    """Close global cache instance"""
    global _cache_instance
    if _cache_instance:
        _cache_instance.close()
        _cache_instance = None
