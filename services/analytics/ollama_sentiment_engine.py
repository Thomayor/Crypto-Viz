"""
Ollama Sentiment Engine
Wrapper simplifié pour l'analyse de sentiment avec Ollama et cache DuckDB.
Optimisé pour gemma3:4b et intégration Kafka.
"""

import logging
import os
from typing import Dict, Any, Optional
import yaml

from ollama_client import OllamaClient, OllamaClientError
from cache_manager import DuckDBCacheManager
from fallback_sentiment import FallbackSentimentClassifier
from sentiment_analyzer import TextPreprocessor

logger = logging.getLogger(__name__)


class OllamaSentimentEngine:
    """
    Moteur d'analyse de sentiment simplifié pour intégration Kafka.

    Features:
    - Analyse de sentiment avec Ollama (gemma3:4b)
    - Cache DuckDB pour éviter re-calculs
    - Fallback rule-based si Ollama fail
    - Interface simple pour Kafka consumer
    """

    def __init__(
        self,
        ollama_url: str = None,
        model: str = None,
        duckdb_path: str = None,
        config_path: str = "config/analytics_config.yaml",
        cache_enabled: bool = True
    ):
        """
        Initialize sentiment engine.

        Args:
            ollama_url: URL Ollama API (default from env)
            model: Model name (default gemma3:4b)
            duckdb_path: Path to DuckDB database
            config_path: Path to YAML config
            cache_enabled: Enable DuckDB caching
        """
        # Load config
        self.config = self._load_config(config_path)

        # Override with params if provided
        ollama_config = self.config.get('ollama', {})
        self.ollama_url = ollama_url or ollama_config.get('url', os.getenv('OLLAMA_URL', 'http://ollama:11434'))
        self.model = model or ollama_config.get('model', os.getenv('OLLAMA_MODEL', 'gemma3:4b'))

        duckdb_config = self.config.get('bootstrap_stack', {}).get('duckdb', {})
        self.duckdb_path = duckdb_path or duckdb_config.get('database_path', '/app/data/crypto_analytics.db')

        self.cache_enabled = cache_enabled
        self.prompt_template = ollama_config.get('prompts', {}).get('sentiment', '')
        self.confidence_threshold = ollama_config.get('sentiment', {}).get('confidence_threshold', 0.5)

        # Initialize components
        self._init_ollama_client()
        self._init_cache_manager()
        self._init_fallback_classifier()

        # Statistics
        self.stats = {
            'total_analyzed': 0,
            'cache_hits': 0,
            'ollama_success': 0,
            'fallback_used': 0,
            'errors': 0
        }

        logger.info(
            f"Sentiment engine initialized: model={self.model}, "
            f"cache={'enabled' if self.cache_enabled else 'disabled'}"
        )

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load YAML configuration"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.debug(f"Config loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def _init_ollama_client(self):
        """Initialize Ollama HTTP client"""
        try:
            self.ollama_client = OllamaClient(
                base_url=self.ollama_url,
                model=self.model,
                timeout=self.config.get('ollama', {}).get('timeout', 30),
                temperature=self.config.get('ollama', {}).get('temperature', 0.0),
                max_tokens=self.config.get('ollama', {}).get('max_tokens', 150),
                max_retries=3
            )

            # Test connectivity
            if self.ollama_client.health_check():
                logger.info(f"✓ Ollama connected: {self.model}")
                self.ollama_available = True
            else:
                logger.warning(f"⚠ Ollama health check failed, will use fallback")
                self.ollama_available = False

        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            self.ollama_client = None
            self.ollama_available = False

    def _init_cache_manager(self):
        """Initialize DuckDB cache manager"""
        if not self.cache_enabled:
            self.cache_manager = None
            return

        try:
            self.cache_manager = DuckDBCacheManager(
                db_path=self.duckdb_path,
                cache_ttl=self.config.get('ollama', {}).get('sentiment', {}).get('cache_ttl', 3600),
                max_cache_size=100000
            )
            logger.info("✓ DuckDB cache manager initialized")
        except Exception as e:
            logger.warning(f"Cache manager init failed: {e}, caching disabled")
            self.cache_manager = None

    def _init_fallback_classifier(self):
        """Initialize fallback classifier"""
        try:
            self.fallback_classifier = FallbackSentimentClassifier(
                confidence_penalty=0.3
            )
            logger.info("✓ Fallback classifier initialized")
        except Exception as e:
            logger.error(f"Failed to initialize fallback classifier: {e}")
            self.fallback_classifier = None

    def analyze_text(
        self,
        text: str,
        source_type: str = 'news',
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze
            source_type: Type of source ('news', 'social', 'post')
            metadata: Optional metadata dict

        Returns:
            Dict with:
            - sentiment_score: float (-1.0 to 1.0)
            - sentiment_label: str ('POSITIVE', 'NEGATIVE', 'NEUTRAL')
            - confidence: float (0.0 to 1.0)
            - keywords: list of str
            - from_cache: bool
            - method: str ('ollama' or 'fallback')
        """
        self.stats['total_analyzed'] += 1

        # Validate and clean text
        cleaned_text = TextPreprocessor.clean_text(text)
        if not TextPreprocessor.validate_text(cleaned_text):
            logger.debug(f"Invalid text (too short/long): {len(text)} chars")
            return self._neutral_result()

        # Check cache first
        if self.cache_enabled and self.cache_manager:
            cached = self.cache_manager.get(cleaned_text, self.model)
            if cached and not cached.is_expired(self.cache_manager.cache_ttl):
                self.stats['cache_hits'] += 1
                return self._format_cached_result(cached)

        # Try Ollama analysis
        if self.ollama_available and self.ollama_client:
            try:
                result = self._analyze_with_ollama(cleaned_text)
                if result:
                    self.stats['ollama_success'] += 1

                    # Store in cache
                    if self.cache_enabled and self.cache_manager:
                        self.cache_manager.put(
                            text=cleaned_text,
                            sentiment=result['sentiment_label'],
                            confidence=result['confidence'],
                            keywords=result['keywords'],
                            model_version=self.model
                        )

                    return result

            except OllamaClientError as e:
                logger.warning(f"Ollama analysis failed: {e}, using fallback")
                self.stats['errors'] += 1

        # Fallback to rule-based classifier
        return self._analyze_with_fallback(cleaned_text)

    def _analyze_with_ollama(self, text: str) -> Optional[Dict[str, Any]]:
        """Analyze with Ollama API"""
        try:
            response = self.ollama_client.analyze_sentiment(
                text=text,
                prompt_template=self.prompt_template
            )

            if not response.is_valid():
                logger.warning("Invalid Ollama response")
                return None

            # Convert sentiment to score
            sentiment_map = {
                'POSITIVE': 1.0,
                'NEGATIVE': -1.0,
                'NEUTRAL': 0.0
            }

            sentiment_score = sentiment_map.get(response.sentiment, 0.0) * response.confidence

            return {
                'sentiment_score': sentiment_score,
                'sentiment_label': response.sentiment,
                'confidence': response.confidence,
                'keywords': response.keywords,
                'from_cache': False,
                'method': 'ollama'
            }

        except Exception as e:
            import traceback
            logger.error(f"Ollama analysis error: {repr(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            return None

    def _analyze_with_fallback(self, text: str) -> Dict[str, Any]:
        """Analyze with fallback classifier"""
        self.stats['fallback_used'] += 1

        if not self.fallback_classifier:
            return self._neutral_result()

        try:
            result = self.fallback_classifier.analyze(text)

            # Convert sentiment to score
            sentiment_map = {
                'POSITIVE': 1.0,
                'NEGATIVE': -1.0,
                'NEUTRAL': 0.0
            }

            sentiment_score = sentiment_map.get(result.sentiment, 0.0) * result.confidence

            return {
                'sentiment_score': sentiment_score,
                'sentiment_label': result.sentiment,
                'confidence': result.confidence,
                'keywords': result.keywords,
                'from_cache': False,
                'method': 'fallback'
            }

        except Exception as e:
            logger.error(f"Fallback analysis error: {e}")
            return self._neutral_result()

    def _format_cached_result(self, cached) -> Dict[str, Any]:
        """Format cached result"""
        sentiment_map = {
            'POSITIVE': 1.0,
            'NEGATIVE': -1.0,
            'NEUTRAL': 0.0
        }

        sentiment_score = sentiment_map.get(cached.sentiment, 0.0) * cached.confidence

        return {
            'sentiment_score': sentiment_score,
            'sentiment_label': cached.sentiment,
            'confidence': cached.confidence,
            'keywords': cached.keywords,
            'from_cache': True,
            'method': 'cache'
        }

    def _neutral_result(self) -> Dict[str, Any]:
        """Return neutral sentiment result"""
        return {
            'sentiment_score': 0.0,
            'sentiment_label': 'NEUTRAL',
            'confidence': 0.5,
            'keywords': [],
            'from_cache': False,
            'method': 'default'
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        stats = self.stats.copy()

        if stats['total_analyzed'] > 0:
            stats['cache_hit_rate'] = stats['cache_hits'] / stats['total_analyzed']
            stats['ollama_success_rate'] = stats['ollama_success'] / stats['total_analyzed']
            stats['fallback_rate'] = stats['fallback_used'] / stats['total_analyzed']
        else:
            stats['cache_hit_rate'] = 0.0
            stats['ollama_success_rate'] = 0.0
            stats['fallback_rate'] = 0.0

        return stats

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_analyzed': 0,
            'cache_hits': 0,
            'ollama_success': 0,
            'fallback_used': 0,
            'errors': 0
        }

    def close(self):
        """Cleanup resources"""
        if self.ollama_client:
            self.ollama_client.close()
        if self.cache_manager:
            self.cache_manager.close()
        logger.info("Sentiment engine closed")


# Standalone usage example
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize engine
    engine = OllamaSentimentEngine()

    # Test texts
    test_texts = [
        ("Bitcoin price surges to new all-time high! 🚀", "news"),
        ("Ethereum network experiencing major issues, users reporting losses", "news"),
        ("BTC holding steady around $50k, market waiting for direction", "social"),
    ]

    print("\n=== Ollama Sentiment Engine Test ===\n")

    for text, source in test_texts:
        result = engine.analyze_text(text, source_type=source)

        print(f"Text: {text}")
        print(f"  Sentiment: {result['sentiment_label']} ({result['sentiment_score']:.2f})")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Keywords: {result['keywords']}")
        print(f"  Method: {result['method']}")
        print(f"  From cache: {result['from_cache']}")
        print()

    # Show stats
    stats = engine.get_stats()
    print("\n=== Statistics ===")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2%}")
        else:
            print(f"  {key}: {value}")

    engine.close()
