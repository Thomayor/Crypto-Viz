"""
DuckDB Cache Manager for Sentiment Analysis
Provides caching layer to avoid re-computing sentiment for identical texts.
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import duckdb

logger = logging.getLogger(__name__)


@dataclass
class CachedSentiment:
    """Cached sentiment result"""
    text_hash: str
    sentiment: str
    confidence: float
    keywords: List[str]
    model_version: str
    created_at: datetime

    def is_expired(self, ttl_seconds: int) -> bool:
        """Check if cache entry is expired"""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'text_hash': self.text_hash,
            'sentiment': self.sentiment,
            'confidence': self.confidence,
            'keywords': self.keywords,
            'model_version': self.model_version,
            'created_at': self.created_at.isoformat()
        }


class CacheManagerError(Exception):
    """Base exception for cache manager errors"""
    pass


class DuckDBCacheManager:
    """
    DuckDB-based cache manager for sentiment analysis results.

    Features:
    - MD5 hashing for text deduplication
    - TTL-based expiration
    - Efficient lookups with indexed queries
    - Batch operations support
    - Cache statistics tracking
    """

    def __init__(
        self,
        db_path: str,
        cache_ttl: int = 3600,
        max_cache_size: int = 100000
    ):
        """
        Initialize cache manager.

        Args:
            db_path: Path to DuckDB database file
            cache_ttl: Time-to-live for cache entries in seconds (default: 1 hour)
            max_cache_size: Maximum number of cached entries before cleanup
        """
        self.db_path = db_path
        self.cache_ttl = cache_ttl
        self.max_cache_size = max_cache_size
        self.connection: Optional[duckdb.DuckDBPyConnection] = None

        # Statistics
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_inserts': 0,
            'cache_evictions': 0,
            'cache_errors': 0
        }

        self._connect()
        self._ensure_schema()

        logger.info(
            f"Cache manager initialized: db={db_path}, ttl={cache_ttl}s, "
            f"max_size={max_cache_size}"
        )

    def _connect(self):
        """Establish connection to DuckDB"""
        try:
            self.connection = duckdb.connect(self.db_path)
            logger.debug(f"Connected to DuckDB: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to DuckDB: {e}")
            raise CacheManagerError(f"Database connection failed: {e}") from e

    def _ensure_schema(self):
        """
        Ensure cache table exists with proper schema.
        The table is created by entrypoint.sh, this is a safety check.
        """
        try:
            # Check if table exists
            result = self.connection.execute("""
                SELECT COUNT(*) as count
                FROM information_schema.tables
                WHERE table_name = 'ollama_sentiment_cache'
            """).fetchone()

            if result[0] == 0:
                logger.warning("Cache table doesn't exist, creating it")
                self.connection.execute("""
                    CREATE TABLE ollama_sentiment_cache (
                        text_hash VARCHAR(32) PRIMARY KEY,
                        sentiment VARCHAR(10) NOT NULL,
                        confidence DECIMAL(3,2) NOT NULL,
                        keywords TEXT,
                        model_version VARCHAR(20),
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                logger.info("Cache table created")
            else:
                logger.debug("Cache table exists")

        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            raise CacheManagerError(f"Schema error: {e}") from e

    @staticmethod
    def hash_text(text: str) -> str:
        """
        Generate MD5 hash for text.

        Args:
            text: Text to hash

        Returns:
            str: MD5 hash (32 chars)
        """
        # Normalize text: strip whitespace, lowercase for consistent hashing
        normalized = text.strip().lower()
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    def get(self, text: str, model_version: str) -> Optional[CachedSentiment]:
        """
        Retrieve cached sentiment for text.

        Args:
            text: Text to look up
            model_version: Model version (must match for cache hit)

        Returns:
            CachedSentiment if found and not expired, None otherwise
        """
        try:
            text_hash = self.hash_text(text)

            # Query cache
            result = self.connection.execute("""
                SELECT
                    text_hash,
                    sentiment,
                    confidence,
                    keywords,
                    model_version,
                    created_at
                FROM ollama_sentiment_cache
                WHERE text_hash = ?
                  AND model_version = ?
            """, [text_hash, model_version]).fetchone()

            if result is None:
                self.stats['cache_misses'] += 1
                logger.debug(f"Cache miss: hash={text_hash[:8]}...")
                return None

            # Parse result
            cached = CachedSentiment(
                text_hash=result[0],
                sentiment=result[1],
                confidence=float(result[2]),
                keywords=result[3].split(',') if result[3] else [],
                model_version=result[4],
                created_at=result[5]
            )

            # Check expiration
            if cached.is_expired(self.cache_ttl):
                logger.debug(f"Cache expired: hash={text_hash[:8]}...")
                self.stats['cache_misses'] += 1
                # Delete expired entry
                self.delete(text_hash)
                return None

            self.stats['cache_hits'] += 1
            logger.debug(
                f"Cache hit: hash={text_hash[:8]}..., sentiment={cached.sentiment}"
            )
            return cached

        except Exception as e:
            self.stats['cache_errors'] += 1
            logger.error(f"Cache lookup error: {e}")
            return None  # Graceful degradation

    def put(
        self,
        text: str,
        sentiment: str,
        confidence: float,
        keywords: List[str],
        model_version: str
    ) -> bool:
        """
        Store sentiment in cache.

        Args:
            text: Original text
            sentiment: Sentiment label (POSITIVE/NEGATIVE/NEUTRAL)
            confidence: Confidence score (0.0-1.0)
            keywords: Extracted keywords
            model_version: Model version used

        Returns:
            bool: True if stored successfully, False otherwise
        """
        try:
            text_hash = self.hash_text(text)
            keywords_str = ','.join(keywords) if keywords else ''

            # Insert or replace
            self.connection.execute("""
                INSERT INTO ollama_sentiment_cache
                    (text_hash, sentiment, confidence, keywords, model_version, created_at)
                VALUES (?, ?, ?, ?, ?, NOW())
                ON CONFLICT (text_hash)
                DO UPDATE SET
                    sentiment = EXCLUDED.sentiment,
                    confidence = EXCLUDED.confidence,
                    keywords = EXCLUDED.keywords,
                    model_version = EXCLUDED.model_version,
                    created_at = EXCLUDED.created_at
            """, [text_hash, sentiment, confidence, keywords_str, model_version])

            self.stats['cache_inserts'] += 1
            logger.debug(
                f"Cache stored: hash={text_hash[:8]}..., sentiment={sentiment}"
            )

            # Check cache size and cleanup if needed
            self._cleanup_if_needed()

            return True

        except Exception as e:
            self.stats['cache_errors'] += 1
            logger.error(f"Cache insert error: {e}")
            return False

    def delete(self, text_hash: str) -> bool:
        """
        Delete cache entry by hash.

        Args:
            text_hash: MD5 hash of text

        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            self.connection.execute("""
                DELETE FROM ollama_sentiment_cache
                WHERE text_hash = ?
            """, [text_hash])
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def get_batch(
        self,
        texts: List[str],
        model_version: str
    ) -> Dict[str, Optional[CachedSentiment]]:
        """
        Retrieve cached sentiments for multiple texts.

        Args:
            texts: List of texts to look up
            model_version: Model version

        Returns:
            Dictionary mapping text to cached sentiment (None if not cached)
        """
        results = {}

        # Generate hashes
        text_to_hash = {text: self.hash_text(text) for text in texts}
        hashes = list(text_to_hash.values())

        try:
            # Batch query
            placeholders = ','.join(['?' for _ in hashes])
            query = f"""
                SELECT
                    text_hash,
                    sentiment,
                    confidence,
                    keywords,
                    model_version,
                    created_at
                FROM ollama_sentiment_cache
                WHERE text_hash IN ({placeholders})
                  AND model_version = ?
            """

            rows = self.connection.execute(
                query,
                hashes + [model_version]
            ).fetchall()

            # Build hash-to-result mapping
            cached_by_hash = {}
            for row in rows:
                cached = CachedSentiment(
                    text_hash=row[0],
                    sentiment=row[1],
                    confidence=float(row[2]),
                    keywords=row[3].split(',') if row[3] else [],
                    model_version=row[4],
                    created_at=row[5]
                )

                # Check expiration
                if not cached.is_expired(self.cache_ttl):
                    cached_by_hash[row[0]] = cached

            # Map back to texts
            for text, text_hash in text_to_hash.items():
                if text_hash in cached_by_hash:
                    results[text] = cached_by_hash[text_hash]
                    self.stats['cache_hits'] += 1
                else:
                    results[text] = None
                    self.stats['cache_misses'] += 1

            hit_rate = self.stats['cache_hits'] / len(texts) if texts else 0
            logger.debug(
                f"Batch cache lookup: {len(texts)} items, hit rate: {hit_rate:.1%}"
            )

        except Exception as e:
            self.stats['cache_errors'] += 1
            logger.error(f"Batch cache lookup error: {e}")
            # Return all None on error
            results = {text: None for text in texts}

        return results

    def _cleanup_if_needed(self):
        """Remove old entries if cache size exceeds limit"""
        try:
            # Check current size
            result = self.connection.execute("""
                SELECT COUNT(*) FROM ollama_sentiment_cache
            """).fetchone()

            current_size = result[0]

            if current_size > self.max_cache_size:
                # Delete oldest 20% of entries
                entries_to_delete = int(self.max_cache_size * 0.2)

                self.connection.execute(f"""
                    DELETE FROM ollama_sentiment_cache
                    WHERE text_hash IN (
                        SELECT text_hash
                        FROM ollama_sentiment_cache
                        ORDER BY created_at ASC
                        LIMIT {entries_to_delete}
                    )
                """)

                self.stats['cache_evictions'] += entries_to_delete
                logger.info(
                    f"Cache cleanup: removed {entries_to_delete} old entries, "
                    f"size: {current_size} -> {current_size - entries_to_delete}"
                )

        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")

    def clear_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            int: Number of entries removed
        """
        try:
            cutoff = datetime.now() - timedelta(seconds=self.cache_ttl)

            result = self.connection.execute("""
                DELETE FROM ollama_sentiment_cache
                WHERE created_at < ?
            """, [cutoff])

            deleted = result.fetchone()[0] if result else 0
            self.stats['cache_evictions'] += deleted

            logger.info(f"Cleared {deleted} expired cache entries")
            return deleted

        except Exception as e:
            logger.error(f"Clear expired error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        stats = self.stats.copy()

        # Calculate hit rate
        total_lookups = stats['cache_hits'] + stats['cache_misses']
        if total_lookups > 0:
            stats['hit_rate'] = stats['cache_hits'] / total_lookups
        else:
            stats['hit_rate'] = 0.0

        # Get cache size
        try:
            result = self.connection.execute("""
                SELECT COUNT(*) FROM ollama_sentiment_cache
            """).fetchone()
            stats['cache_size'] = result[0]

            # Get oldest entry age
            result = self.connection.execute("""
                SELECT MIN(created_at) FROM ollama_sentiment_cache
            """).fetchone()

            if result[0]:
                age = (datetime.now() - result[0]).total_seconds()
                stats['oldest_entry_age_seconds'] = age
            else:
                stats['oldest_entry_age_seconds'] = 0

        except Exception as e:
            logger.error(f"Stats query error: {e}")

        return stats

    def reset_stats(self):
        """Reset statistics counters"""
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_inserts': 0,
            'cache_evictions': 0,
            'cache_errors': 0
        }
        logger.info("Cache statistics reset")

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Cache manager connection closed")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize cache manager
    cache = DuckDBCacheManager(
        db_path="/tmp/test_cache.db",
        cache_ttl=3600,
        max_cache_size=10000
    )

    # Test storing and retrieving
    text = "Bitcoin is showing strong bullish momentum!"
    model = "llama3.1:8b"

    # Store in cache
    cache.put(
        text=text,
        sentiment="POSITIVE",
        confidence=0.89,
        keywords=["bitcoin", "bullish", "momentum"],
        model_version=model
    )

    # Retrieve from cache
    cached = cache.get(text, model)
    if cached:
        print(f"Cached result found:")
        print(f"  Sentiment: {cached.sentiment}")
        print(f"  Confidence: {cached.confidence}")
        print(f"  Keywords: {cached.keywords}")
    else:
        print("Cache miss")

    # Show stats
    stats = cache.get_stats()
    print(f"\nCache stats: {stats}")

    cache.close()
