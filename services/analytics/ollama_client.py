"""
Ollama Client for Sentiment Analysis
Handles HTTP communication with Ollama API with robust error handling and retry logic.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)


@dataclass
class OllamaResponse:
    """Structured response from Ollama API"""
    sentiment: str
    confidence: float
    keywords: List[str]
    raw_response: str
    processing_time: float
    model_used: str

    def is_valid(self) -> bool:
        """Validate response data"""
        valid_sentiments = ["POSITIVE", "NEGATIVE", "NEUTRAL"]
        return (
            self.sentiment in valid_sentiments and
            0.0 <= self.confidence <= 1.0 and
            isinstance(self.keywords, list)
        )


class OllamaClientError(Exception):
    """Base exception for Ollama client errors"""
    pass


class OllamaConnectionError(OllamaClientError):
    """Raised when connection to Ollama fails"""
    pass


class OllamaTimeoutError(OllamaClientError):
    """Raised when Ollama request times out"""
    pass


class OllamaParsingError(OllamaClientError):
    """Raised when response parsing fails"""
    pass


class OllamaClient:
    """
    HTTP client for Ollama API with robust error handling.

    Features:
    - Connection pooling and keep-alive
    - Automatic retries with exponential backoff
    - Response validation and parsing
    - Timeout handling
    - Circuit breaker pattern support
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: int = 30,
        temperature: float = 0.1,
        max_tokens: int = 100,
        max_retries: int = 3
    ):
        """
        Initialize Ollama client.

        Args:
            base_url: Base URL for Ollama API (e.g., http://ollama:11434)
            model: Model name (e.g., llama3.1:8b)
            timeout: Request timeout in seconds
            temperature: Model temperature (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum tokens in response
            max_retries: Maximum retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries

        # Setup session with connection pooling
        self.session = self._create_session()

        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens': 0,
            'total_processing_time': 0.0
        }

        logger.info(
            f"Ollama client initialized: url={base_url}, model={model}, "
            f"timeout={timeout}s, temperature={temperature}"
        )

    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy"""
        session = requests.Session()

        # Retry strategy for transient errors
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP codes
            allowed_methods=["POST"]
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20,
            pool_block=False
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def health_check(self) -> bool:
        """
        Check if Ollama service is healthy and model is available.

        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            # Check API availability
            response = self.session.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()

            # Check if model exists
            models_data = response.json()
            available_models = [m['name'] for m in models_data.get('models', [])]

            if self.model not in available_models:
                logger.warning(
                    f"Model {self.model} not found. Available: {available_models}"
                )
                return False

            logger.info(f"Ollama health check passed. Model {self.model} available.")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((OllamaConnectionError, OllamaTimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def analyze_sentiment(
        self,
        text: str,
        prompt_template: str
    ) -> OllamaResponse:
        """
        Analyze sentiment of text using Ollama.

        Args:
            text: Text to analyze
            prompt_template: Prompt template with {text} placeholder

        Returns:
            OllamaResponse: Structured sentiment analysis result

        Raises:
            OllamaConnectionError: If connection fails
            OllamaTimeoutError: If request times out
            OllamaParsingError: If response parsing fails
        """
        start_time = time.time()
        self.stats['total_requests'] += 1

        try:
            # Format prompt
            prompt = prompt_template.format(text=text)
            logger.info(f"[OLLAMA DEBUG] Formatted prompt (first 200 chars): {prompt[:200]}")

            # Prepare request
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            }
            logger.info(f"[OLLAMA DEBUG] Payload prepared: model={self.model}, temp={self.temperature}")

            # Make request
            logger.info(f"[OLLAMA DEBUG] Sending POST to {self.base_url}/api/generate")
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            logger.info(f"[OLLAMA DEBUG] Response received: status={response.status_code}")

            # Check HTTP status
            response.raise_for_status()
            logger.info(f"[OLLAMA DEBUG] HTTP status OK")

            # Parse response
            response_data = response.json()
            logger.info(f"[OLLAMA DEBUG] Response JSON keys: {list(response_data.keys())}")
            raw_text = response_data.get('response', '').strip()
            logger.info(f"[OLLAMA DEBUG] Raw Ollama response (full): {raw_text}")

            processing_time = time.time() - start_time
            self.stats['total_processing_time'] += processing_time
            logger.info(f"[OLLAMA DEBUG] Processing time: {processing_time:.2f}s")

            # Parse JSON from response
            logger.info(f"[OLLAMA DEBUG] Calling _parse_response...")
            ollama_response = self._parse_response(
                raw_text,
                processing_time,
                self.model
            )
            logger.info(f"[OLLAMA DEBUG] _parse_response completed successfully")

            # Validate response
            if not ollama_response.is_valid():
                raise OllamaParsingError(
                    f"Invalid response data: {ollama_response}"
                )

            self.stats['successful_requests'] += 1
            logger.debug(
                f"Sentiment analysis successful: sentiment={ollama_response.sentiment}, "
                f"confidence={ollama_response.confidence:.2f}, time={processing_time:.2f}s"
            )

            return ollama_response

        except requests.exceptions.Timeout as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Ollama request timeout after {self.timeout}s: {e}")
            raise OllamaTimeoutError(f"Request timed out: {e}") from e

        except requests.exceptions.ConnectionError as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Ollama connection error: {e}")
            raise OllamaConnectionError(f"Connection failed: {e}") from e

        except requests.exceptions.RequestException as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Ollama request failed: {e}")
            raise OllamaConnectionError(f"Request failed: {e}") from e

        except OllamaParsingError:
            self.stats['failed_requests'] += 1
            raise

        except Exception as e:
            self.stats['failed_requests'] += 1
            import traceback
            logger.error(f"Unexpected error in Ollama client: {repr(e)}\nType: {type(e)}\nTraceback: {traceback.format_exc()}")
            raise OllamaClientError(f"Unexpected error: {e}") from e

    def _parse_response(
        self,
        raw_text: str,
        processing_time: float,
        model: str
    ) -> OllamaResponse:
        """
        Parse JSON response from Ollama with robust error handling.

        Args:
            raw_text: Raw response text from Ollama
            processing_time: Time taken to process
            model: Model used

        Returns:
            OllamaResponse: Parsed response

        Raises:
            OllamaParsingError: If parsing fails
        """
        try:
            logger.info(f"[PARSE DEBUG] Starting parse, raw_text length: {len(raw_text)}")
            logger.info(f"[PARSE DEBUG] Raw text: {raw_text}")

            # Try to find JSON in response
            # Sometimes Ollama adds text before/after JSON
            json_start = raw_text.find('{')
            json_end = raw_text.rfind('}') + 1
            logger.info(f"[PARSE DEBUG] JSON positions: start={json_start}, end={json_end}")

            if json_start == -1 or json_end == 0:
                logger.error(f"[PARSE DEBUG] No JSON braces found in: {raw_text[:200]}")
                raise OllamaParsingError(
                    f"No JSON found in response: {raw_text[:200]}"
                )

            json_str = raw_text[json_start:json_end]
            logger.info(f"[PARSE DEBUG] Extracted JSON string: {json_str}")

            data = json.loads(json_str)
            logger.info(f"[PARSE DEBUG] json.loads() returned type: {type(data)}, value: {data}")

            # Ensure data is a dictionary
            if not isinstance(data, dict):
                logger.error(f"[PARSE DEBUG] Data is {type(data).__name__}, not dict!")
                raise OllamaParsingError(
                    f"JSON is not an object (got {type(data).__name__}): {data}"
                )

            logger.info(f"[PARSE DEBUG] Data is dict, keys: {list(data.keys())}")

            # Extract fields with defaults
            sentiment = data.get('sentiment', 'NEUTRAL').upper()
            confidence = float(data.get('confidence', 0.5))
            keywords = data.get('keywords', [])
            logger.info(f"[PARSE DEBUG] Extracted: sentiment={sentiment}, confidence={confidence}, keywords={keywords}")

            # Ensure keywords is a list
            if not isinstance(keywords, list):
                keywords = []

            return OllamaResponse(
                sentiment=sentiment,
                confidence=confidence,
                keywords=keywords,
                raw_response=raw_text,
                processing_time=processing_time,
                model_used=model
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}. Raw text: {raw_text[:200]}")
            raise OllamaParsingError(f"Invalid JSON: {e}") from e

        except (ValueError, TypeError) as e:
            logger.error(f"Data conversion error: {e}")
            raise OllamaParsingError(f"Data parsing error: {e}") from e

    def analyze_batch(
        self,
        texts: List[str],
        prompt_template: str
    ) -> List[Optional[OllamaResponse]]:
        """
        Analyze multiple texts sequentially.

        Args:
            texts: List of texts to analyze
            prompt_template: Prompt template with {text} placeholder

        Returns:
            List of OllamaResponse objects (None for failed analyses)
        """
        results = []

        for i, text in enumerate(texts):
            try:
                result = self.analyze_sentiment(text, prompt_template)
                results.append(result)
                logger.debug(f"Batch item {i+1}/{len(texts)} analyzed successfully")

            except OllamaClientError as e:
                logger.warning(f"Batch item {i+1}/{len(texts)} failed: {e}")
                results.append(None)

        success_rate = sum(1 for r in results if r is not None) / len(results)
        logger.info(
            f"Batch analysis completed: {len(results)} items, "
            f"success rate: {success_rate:.1%}"
        )

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        stats = self.stats.copy()

        if stats['successful_requests'] > 0:
            stats['avg_processing_time'] = (
                stats['total_processing_time'] / stats['successful_requests']
            )
        else:
            stats['avg_processing_time'] = 0.0

        if stats['total_requests'] > 0:
            stats['success_rate'] = (
                stats['successful_requests'] / stats['total_requests']
            )
        else:
            stats['success_rate'] = 0.0

        return stats

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_tokens': 0,
            'total_processing_time': 0.0
        }
        logger.info("Ollama client statistics reset")

    def close(self):
        """Close the session and cleanup resources"""
        if self.session:
            self.session.close()
            logger.info("Ollama client session closed")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Initialize client
    client = OllamaClient(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        timeout=30,
        temperature=0.1
    )

    # Health check
    if not client.health_check():
        logger.error("Ollama service not available")
        exit(1)

    # Test sentiment analysis
    prompt = """Analyse le sentiment de ce texte concernant les cryptomonnaies.
Réponds UNIQUEMENT avec ce format JSON exact :
{"sentiment": "POSITIVE|NEGATIVE|NEUTRAL", "confidence": 0.85, "keywords": ["bitcoin", "bullish"]}

Texte à analyser: {text}

JSON:"""

    test_text = "Bitcoin is showing strong bullish momentum! 🚀 Price breaking resistance."

    try:
        result = client.analyze_sentiment(test_text, prompt)
        print(f"\nResult:")
        print(f"  Sentiment: {result.sentiment}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Keywords: {result.keywords}")
        print(f"  Processing time: {result.processing_time:.2f}s")

        stats = client.get_stats()
        print(f"\nStats: {stats}")

    except OllamaClientError as e:
        print(f"Error: {e}")

    finally:
        client.close()
