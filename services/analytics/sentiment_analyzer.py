"""
Ollama Sentiment Engine
Main orchestrator for sentiment analysis with Ollama and DuckDB caching.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import time

from ollama_client import OllamaClient, OllamaResponse, OllamaClientError
from cache_manager import DuckDBCacheManager, CachedSentiment

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """Result of sentiment analysis"""
    text: str
    sentiment: str
    confidence: float
    keywords: List[str]
    from_cache: bool
    processing_time: float
    model_used: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'text': self.text[:100] + '...' if len(self.text) > 100 else self.text,
            'sentiment': self.sentiment,
            'confidence': self.confidence,
            'keywords': self.keywords,
            'from_cache': self.from_cache,
            'processing_time': self.processing_time,
            'model_used': self.model_used
        }


class TextPreprocessor:
    """Utilities for text preprocessing before sentiment analysis"""

    # Crypto-related keywords for context
    CRYPTO_KEYWORDS = {
        'bitcoin': 'BTC', 'btc': 'BTC',
        'ethereum': 'ETH', 'eth': 'ETH',
        'cardano': 'ADA', 'ada': 'ADA',
        'ripple': 'XRP', 'xrp': 'XRP',
        'dogecoin': 'DOGE', 'doge': 'DOGE',
        'polkadot': 'DOT', 'dot': 'DOT',
        'solana': 'SOL', 'sol': 'SOL',
        'avalanche': 'AVAX', 'avax': 'AVAX',
    }

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text for analysis.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove URLs
        text = re.sub(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            '',
            text
        )

        # Remove user mentions and hashtags (but keep the text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#(\w+)', r'\1', text)  # Keep hashtag text

        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text.strip()

    @classmethod
    def extract_coins(cls, text: str) -> List[str]:
        """
        Extract cryptocurrency mentions from text.

        Args:
            text: Text to analyze

        Returns:
            List of coin symbols found
        """
        text_lower = text.lower()
        coins_found = set()

        for keyword, symbol in cls.CRYPTO_KEYWORDS.items():
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                coins_found.add(symbol)

        return sorted(list(coins_found))

    @staticmethod
    def validate_text(text: str, min_length: int = 10, max_length: int = 5000) -> bool:
        """
        Validate text is suitable for analysis.

        Args:
            text: Text to validate
            min_length: Minimum acceptable length
            max_length: Maximum acceptable length

        Returns:
            True if valid, False otherwise
        """
        if not text or not isinstance(text, str):
            return False

        text_len = len(text.strip())
        return min_length <= text_len <= max_length


class OllamaSentimentEngine:
    """
    Main sentiment analysis engine with Ollama and DuckDB cache.

    Features:
    - Batch processing with configurable batch size
    - DuckDB caching to avoid re-computation
    - Text preprocessing and validation
    - Confidence threshold filtering
    - Comprehensive error handling
    - Performance statistics
    """

    def __init__(
        self,
        ollama_url: str,
        ollama_model: str,
        duckdb_path: str,
        prompt_template: str,
        batch_size: int = 10,
        confidence_threshold: float = 0.6,
        cache_enabled: bool = True,
        cache_ttl: int = 3600,
        ollama_timeout: int = 30,
        ollama_temperature: float = 0.1,
        ollama_max_tokens: int = 100
    ):
        """
        Initialize sentiment engine.

        Args:
            ollama_url: URL for Ollama API
            ollama_model: Model name to use
            duckdb_path: Path to DuckDB database
            prompt_template: Template for sentiment prompts
            batch_size: Number of texts to process in batch
            confidence_threshold: Minimum confidence to accept result
            cache_enabled: Whether to use caching
            cache_ttl: Cache time-to-live in seconds
            ollama_timeout: Timeout for Ollama requests
            ollama_temperature: Model temperature
            ollama_max_tokens: Max tokens in response
        """
        self.batch_size = batch_size
        self.confidence_threshold = confidence_threshold
        self.cache_enabled = cache_enabled
        self.prompt_template = prompt_template

        # Initialize Ollama client
        self.ollama_client = OllamaClient(
            base_url=ollama_url,
            model=ollama_model,
            timeout=ollama_timeout,
            temperature=ollama_temperature,
            max_tokens=ollama_max_tokens
        )

        # Initialize cache manager
        if cache_enabled:
            self.cache_manager = DuckDBCacheManager(
                db_path=duckdb_path,
                cache_ttl=cache_ttl
            )
        else:
            self.cache_manager = None

        # Statistics
        self.stats = {
            'total_analyzed': 0,
            'cache_hits': 0,
            'ollama_calls': 0,
            'below_threshold': 0,
            'errors': 0,
            'total_processing_time': 0.0
        }

        logger.info(
            f"Sentiment engine initialized: model={ollama_model}, "
            f"batch_size={batch_size}, cache_enabled={cache_enabled}"
        )

        # Health check
        if not self.ollama_client.health_check():
            logger.warning("Ollama health check failed - service may not be available")

    def analyze(self, text: str) -> Optional[SentimentResult]:
        """
        Analyze sentiment of a single text.

        Args:
            text: Text to analyze

        Returns:
            SentimentResult or None if analysis fails
        """
        results = self.analyze_batch([text])
        return results[0] if results else None

    def analyze_batch(self, texts: List[str]) -> List[Optional[SentimentResult]]:
        """
        Analyze sentiment of multiple texts with batching and caching.

        Args:
            texts: List of texts to analyze

        Returns:
            List of SentimentResult objects (None for failed analyses)
        """
        start_time = time.time()
        results: List[Optional[SentimentResult]] = []

        # Preprocess and validate texts
        processed_texts = []
        text_indices = []  # Track which original indices are valid

        for i, text in enumerate(texts):
            cleaned = TextPreprocessor.clean_text(text)

            if TextPreprocessor.validate_text(cleaned):
                processed_texts.append((i, text, cleaned))
                text_indices.append(i)
            else:
                logger.debug(f"Text {i} invalid or too short, skipping")

        if not processed_texts:
            logger.warning("No valid texts to analyze in batch")
            return [None] * len(texts)

        # Check cache first (if enabled)
        cache_results = {}
        texts_to_analyze = []

        if self.cache_enabled and self.cache_manager:
            cleaned_texts = [t[2] for t in processed_texts]
            cache_results = self.cache_manager.get_batch(
                cleaned_texts,
                self.ollama_client.model
            )

            # Separate cached vs non-cached
            for idx, orig_text, cleaned in processed_texts:
                cached = cache_results.get(cleaned)
                if cached:
                    # Use cached result
                    result = SentimentResult(
                        text=orig_text,
                        sentiment=cached.sentiment,
                        confidence=cached.confidence,
                        keywords=cached.keywords,
                        from_cache=True,
                        processing_time=0.0,
                        model_used=cached.model_version
                    )
                    results.append((idx, result))
                    self.stats['cache_hits'] += 1
                else:
                    # Need to analyze
                    texts_to_analyze.append((idx, orig_text, cleaned))
        else:
            texts_to_analyze = processed_texts

        logger.debug(
            f"Batch: {len(texts)} total, {len(results)} cached, "
            f"{len(texts_to_analyze)} to analyze"
        )

        # Analyze non-cached texts
        if texts_to_analyze:
            analyzed_results = self._analyze_with_ollama(texts_to_analyze)
            results.extend(analyzed_results)

        # Sort results by original index and create final list
        results.sort(key=lambda x: x[0])
        final_results = [None] * len(texts)

        for idx, result in results:
            final_results[idx] = result

        # Update stats
        self.stats['total_analyzed'] += len(texts)
        total_time = time.time() - start_time
        self.stats['total_processing_time'] += total_time

        success_count = sum(1 for r in final_results if r is not None)
        logger.info(
            f"Batch analysis completed: {len(texts)} texts, "
            f"{success_count} successful, time={total_time:.2f}s"
        )

        return final_results

    def _analyze_with_ollama(
        self,
        texts_data: List[Tuple[int, str, str]]
    ) -> List[Tuple[int, Optional[SentimentResult]]]:
        """
        Analyze texts using Ollama API.

        Args:
            texts_data: List of (index, original_text, cleaned_text) tuples

        Returns:
            List of (index, SentimentResult) tuples
        """
        results = []

        for idx, orig_text, cleaned_text in texts_data:
            try:
                # Call Ollama
                start = time.time()
                ollama_response = self.ollama_client.analyze_sentiment(
                    cleaned_text,
                    self.prompt_template
                )
                processing_time = time.time() - start

                self.stats['ollama_calls'] += 1

                # Check confidence threshold
                if ollama_response.confidence < self.confidence_threshold:
                    logger.debug(
                        f"Confidence {ollama_response.confidence:.2f} below "
                        f"threshold {self.confidence_threshold}, skipping"
                    )
                    self.stats['below_threshold'] += 1
                    results.append((idx, None))
                    continue

                # Create result
                result = SentimentResult(
                    text=orig_text,
                    sentiment=ollama_response.sentiment,
                    confidence=ollama_response.confidence,
                    keywords=ollama_response.keywords,
                    from_cache=False,
                    processing_time=processing_time,
                    model_used=ollama_response.model_used
                )

                results.append((idx, result))

                # Store in cache
                if self.cache_enabled and self.cache_manager:
                    self.cache_manager.put(
                        text=cleaned_text,
                        sentiment=ollama_response.sentiment,
                        confidence=ollama_response.confidence,
                        keywords=ollama_response.keywords,
                        model_version=self.ollama_client.model
                    )

                logger.debug(
                    f"Analyzed: sentiment={result.sentiment}, "
                    f"confidence={result.confidence:.2f}, time={processing_time:.2f}s"
                )

            except OllamaClientError as e:
                logger.error(f"Ollama analysis error: {e}")
                self.stats['errors'] += 1
                results.append((idx, None))

            except Exception as e:
                logger.error(f"Unexpected error in sentiment analysis: {e}")
                self.stats['errors'] += 1
                results.append((idx, None))

        return results

    def analyze_with_coins(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analyze sentiment and extract coin mentions.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with sentiment and coin information
        """
        result = self.analyze(text)

        if result is None:
            return None

        coins = TextPreprocessor.extract_coins(text)

        return {
            'sentiment': result.sentiment,
            'confidence': result.confidence,
            'keywords': result.keywords,
            'coins_mentioned': coins,
            'from_cache': result.from_cache,
            'processing_time': result.processing_time
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics.

        Returns:
            Dictionary with engine, cache, and Ollama stats
        """
        stats = {
            'engine': self.stats.copy(),
            'ollama': self.ollama_client.get_stats(),
        }

        if self.cache_enabled and self.cache_manager:
            stats['cache'] = self.cache_manager.get_stats()

        # Calculate additional metrics
        if stats['engine']['total_analyzed'] > 0:
            stats['engine']['cache_hit_rate'] = (
                stats['engine']['cache_hits'] / stats['engine']['total_analyzed']
            )
            stats['engine']['error_rate'] = (
                stats['engine']['errors'] / stats['engine']['total_analyzed']
            )
            stats['engine']['avg_processing_time'] = (
                stats['engine']['total_processing_time'] /
                stats['engine']['total_analyzed']
            )
        else:
            stats['engine']['cache_hit_rate'] = 0.0
            stats['engine']['error_rate'] = 0.0
            stats['engine']['avg_processing_time'] = 0.0

        return stats

    def reset_stats(self):
        """Reset all statistics"""
        self.stats = {
            'total_analyzed': 0,
            'cache_hits': 0,
            'ollama_calls': 0,
            'below_threshold': 0,
            'errors': 0,
            'total_processing_time': 0.0
        }
        self.ollama_client.reset_stats()
        if self.cache_enabled and self.cache_manager:
            self.cache_manager.reset_stats()
        logger.info("Sentiment engine statistics reset")

    def close(self):
        """Cleanup resources"""
        if self.ollama_client:
            self.ollama_client.close()
        if self.cache_enabled and self.cache_manager:
            self.cache_manager.close()
        logger.info("Sentiment engine closed")


# Example usage
if __name__ == "__main__":
    import yaml

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Load configuration
    with open('config/analytics_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize engine
    engine = OllamaSentimentEngine(
        ollama_url=config['ollama']['url'],
        ollama_model=config['ollama']['model'],
        duckdb_path=config['bootstrap_stack']['duckdb']['database_path'],
        prompt_template=config['ollama']['prompts']['sentiment'],
        batch_size=config['ollama']['sentiment']['batch_size'],
        confidence_threshold=config['ollama']['sentiment']['confidence_threshold'],
        cache_enabled=config['ollama']['sentiment']['cache_enabled'],
        cache_ttl=config['ollama']['sentiment']['cache_ttl'],
        ollama_timeout=config['ollama']['timeout'],
        ollama_temperature=config['ollama']['temperature'],
        ollama_max_tokens=config['ollama']['max_tokens']
    )

    # Test texts
    test_texts = [
        "Bitcoin is showing strong bullish momentum! 🚀",
        "Ethereum dump incoming, sell now!",
        "ADA price stable, waiting for breakout",
        "Crypto market looking good today"
    ]

    # Analyze batch
    print("\n=== Batch Analysis ===")
    results = engine.analyze_batch(test_texts)

    for i, result in enumerate(results):
        if result:
            print(f"\nText {i+1}: {test_texts[i]}")
            print(f"  Sentiment: {result.sentiment}")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Keywords: {result.keywords}")
            print(f"  From cache: {result.from_cache}")
            print(f"  Time: {result.processing_time:.2f}s")

    # Show stats
    print("\n=== Statistics ===")
    stats = engine.get_stats()
    print(f"Engine stats: {stats['engine']}")
    print(f"Cache stats: {stats.get('cache', 'N/A')}")

    engine.close()
