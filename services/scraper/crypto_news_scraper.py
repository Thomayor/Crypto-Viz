#!/usr/bin/env python3
"""
CRYPTO VIZ - Crypto News Scraper Service
Scrapes cryptocurrency news from multiple sources and publishes to Kafka
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

import aiohttp
import requests
from kafka import KafkaProducer
from kafka.errors import KafkaError
from newsapi import NewsApiClient
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import backoff

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NewsSource(Enum):
    """Enumeration of supported news sources"""
    COINMARKETCAP = "coinmarketcap"
    NEWSAPI = "newsapi"
    CRYPTOPANIC = "cryptopanic"


@dataclass
class CryptoNews:
    """Data class for cryptocurrency news"""
    source: str
    title: str
    description: Optional[str]
    url: str
    published_at: str
    author: Optional[str]
    image_url: Optional[str]
    sentiment: Optional[str] = None
    coins_mentioned: Optional[List[str]] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict:
        """Convert to dictionary for Kafka serialization"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class CryptoPrice:
    """Data class for cryptocurrency price data"""
    symbol: str
    name: str
    price: float
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    percent_change_1h: Optional[float] = None
    percent_change_24h: Optional[float] = None
    percent_change_7d: Optional[float] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None
    max_supply: Optional[float] = None
    rank: Optional[int] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict:
        """Convert to dictionary for Kafka serialization"""
        return {k: v for k, v in asdict(self).items() if v is not None}


class RateLimiter:
    """Token bucket rate limiter for API calls"""

    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    async def acquire(self):
        """Acquire permission to make an API call"""
        now = time.time()
        # Remove calls outside the time window
        self.calls = [call_time for call_time in self.calls if call_time > now - self.period]

        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                return await self.acquire()

        self.calls.append(now)
        return True


class CoinMarketCapScraper:
    """Scraper for CoinMarketCap API"""

    BASE_URL = "https://pro-api.coinmarketcap.com"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        # CoinMarketCap free tier: 10,000 calls/month (~333/day, ~14/hour)
        self.rate_limiter = RateLimiter(max_calls=10, period=3600)  # 10 per hour to be safe

    async def __aenter__(self):
        headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        }

        self.session = aiohttp.ClientSession(headers=headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def fetch_trending_coins(self) -> List[Dict]:
        """Fetch trending coins from CoinMarketCap"""
        await self.rate_limiter.acquire()

        url = f"{self.BASE_URL}/v1/cryptocurrency/trending/latest"

        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()

                trending = data.get('data', [])
                logger.info(f"Fetched {len(trending)} trending coins from CoinMarketCap")
                return trending

        except aiohttp.ClientError as e:
            logger.error(f"CoinMarketCap API error: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def fetch_latest_listings(self, limit: int = 100) -> List[Dict]:
        """Fetch latest cryptocurrency listings from CoinMarketCap"""
        await self.rate_limiter.acquire()

        url = f"{self.BASE_URL}/v1/cryptocurrency/listings/latest"
        params = {
            'start': 1,
            'limit': limit,
            'sort': 'market_cap',
            'convert': 'USD'
        }

        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()

                listings = data.get('data', [])
                logger.info(f"Fetched {len(listings)} latest listings from CoinMarketCap")
                return listings

        except aiohttp.ClientError as e:
            logger.error(f"CoinMarketCap listings error: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def fetch_gainers_losers(self) -> Dict[str, List[Dict]]:
        """Fetch top gainers and losers from CoinMarketCap"""
        await self.rate_limiter.acquire()

        url = f"{self.BASE_URL}/v1/cryptocurrency/trending/gainers-losers"

        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()

                logger.info(f"Fetched gainers/losers from CoinMarketCap")
                return data.get('data', {})

        except aiohttp.ClientError as e:
            logger.error(f"CoinMarketCap gainers/losers error: {e}")
            raise


class NewsAPIScraper:
    """Scraper for NewsAPI"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = NewsApiClient(api_key=api_key)
        # NewsAPI free tier: 100 requests/day
        self.rate_limiter = RateLimiter(max_calls=4, period=3600)  # 4 per hour to be safe

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def fetch_crypto_news(self, keywords: List[str] = None, page_size: int = 20) -> List[CryptoNews]:
        """Fetch cryptocurrency news from NewsAPI"""
        await self.rate_limiter.acquire()

        if keywords is None:
            keywords = ['cryptocurrency', 'bitcoin', 'ethereum', 'blockchain', 'crypto']

        query = ' OR '.join(keywords)
        from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        try:
            # Run synchronous API call in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get_everything(
                    q=query,
                    from_param=from_date,
                    language='en',
                    sort_by='publishedAt',
                    page_size=page_size
                )
            )

            articles = response.get('articles', [])

            news_items = []
            for article in articles:
                news = CryptoNews(
                    source=f"newsapi-{article['source']['name']}",
                    title=article['title'],
                    description=article.get('description'),
                    url=article['url'],
                    published_at=article['publishedAt'],
                    author=article.get('author'),
                    image_url=article.get('urlToImage'),
                    coins_mentioned=self._extract_coins_from_text(article['title'] + ' ' + (article.get('description') or ''))
                )
                news_items.append(news)

            logger.info(f"Fetched {len(news_items)} news articles from NewsAPI")
            return news_items

        except Exception as e:
            logger.error(f"NewsAPI error: {e}")
            raise

    @staticmethod
    def _extract_coins_from_text(text: str) -> List[str]:
        """Extract cryptocurrency mentions from text"""
        text_lower = text.lower()
        coins = []

        # Common cryptocurrency keywords
        coin_keywords = {
            'bitcoin': 'BTC',
            'ethereum': 'ETH',
            'cardano': 'ADA',
            'solana': 'SOL',
            'polkadot': 'DOT',
            'ripple': 'XRP',
            'dogecoin': 'DOGE',
            'shiba': 'SHIB',
            'polygon': 'MATIC',
            'avalanche': 'AVAX',
            'chainlink': 'LINK',
            'cosmos': 'ATOM',
            'algorand': 'ALGO',
            'binance': 'BNB'
        }

        for keyword, symbol in coin_keywords.items():
            if keyword in text_lower or symbol.lower() in text_lower:
                coins.append(symbol)

        return list(set(coins))  # Remove duplicates


class KafkaNewsPublisher:
    """Publishes crypto news and prices to Kafka"""

    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer: Optional[KafkaProducer] = None
        self._setup_producer()

    def _setup_producer(self):
        """Initialize Kafka producer with retry logic"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1,
                compression_type='gzip',
                linger_ms=10,
                batch_size=16384
            )
            logger.info(f"Kafka producer connected to {self.bootstrap_servers}")
        except KafkaError as e:
            logger.error(f"Failed to create Kafka producer: {e}")
            raise

    @backoff.on_exception(
        backoff.expo,
        KafkaError,
        max_tries=5,
        max_time=60
    )
    def publish(self, item, topic: str) -> bool:
        """Publish a single item to Kafka (CryptoNews or CryptoPrice)"""
        try:
            # Use appropriate key based on item type
            if hasattr(item, 'url'):
                # CryptoNews - use URL for deduplication
                key = item.url
            elif hasattr(item, 'symbol'):
                # CryptoPrice - use symbol for partitioning
                key = item.symbol
            else:
                # Fallback
                key = str(int(time.time() * 1000))

            value = item.to_dict()

            future = self.producer.send(
                topic,
                key=key,
                value=value,
                timestamp_ms=int(time.time() * 1000)
            )

            # Wait for confirmation (with timeout)
            record_metadata = future.get(timeout=10)

            logger.debug(
                f"Published to Kafka: topic={record_metadata.topic}, "
                f"partition={record_metadata.partition}, offset={record_metadata.offset}"
            )
            return True

        except KafkaError as e:
            logger.error(f"Failed to publish to Kafka: {e}")
            raise

    def publish_batch(self, items: List, topic: str) -> tuple[int, int]:
        """Publish multiple items to Kafka (CryptoNews or CryptoPrice)"""
        success_count = 0
        error_count = 0

        for item in items:
            try:
                self.publish(item, topic)
                success_count += 1
            except Exception as e:
                # Get item identifier based on type
                identifier = getattr(item, 'title', None) or getattr(item, 'symbol', 'unknown')
                logger.error(f"Failed to publish '{identifier}': {e}")
                error_count += 1

        logger.info(f"Published {success_count}/{len(items)} items to {topic} (errors: {error_count})")
        return success_count, error_count

    def close(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka producer closed")


class CryptoNewsScraper:
    """Main orchestrator for crypto news scraping"""

    def __init__(
        self,
        kafka_bootstrap_servers: str,
        newsapi_key: Optional[str] = None,
        coinmarketcap_api_key: Optional[str] = None,
        scrape_interval: int = 30
    ):
        self.kafka_publisher = KafkaNewsPublisher(kafka_bootstrap_servers)
        self.newsapi_key = newsapi_key
        self.coinmarketcap_api_key = coinmarketcap_api_key
        self.scrape_interval = scrape_interval
        self.stats = {
            'total_scraped': 0,
            'total_published': 0,
            'total_errors': 0,
            'last_scrape_time': None
        }

    async def scrape_all_sources(self) -> Dict[str, List[CryptoNews]]:
        """Scrape news and prices from all configured sources"""
        news_items = []
        price_items = []

        # Scrape from NewsAPI if configured
        if self.newsapi_key:
            try:
                newsapi_scraper = NewsAPIScraper(self.newsapi_key)
                articles = await newsapi_scraper.fetch_crypto_news()
                news_items.extend(articles)
                logger.info(f"Scraped {len(articles)} articles from NewsAPI")
            except Exception as e:
                logger.error(f"NewsAPI scraping failed: {e}")
                self.stats['total_errors'] += 1
        else:
            logger.warning("NewsAPI key not configured, skipping NewsAPI scraping")

        # Scrape from CoinMarketCap
        if self.coinmarketcap_api_key:
            try:
                async with CoinMarketCapScraper(self.coinmarketcap_api_key) as cmc_scraper:
                    # Use latest listings instead of trending (free tier compatible)
                    # Configurable via CRYPTO_COUNT env var (default: 6 cryptos, excluding stablecoins)
                    crypto_count = int(os.getenv('CRYPTO_COUNT', '6'))
                    listings = await cmc_scraper.fetch_latest_listings(limit=crypto_count)

                    # Create price items from top listings with proper structure
                    for coin in listings:
                        quote = coin.get('quote', {}).get('USD', {})

                        price_data = CryptoPrice(
                            symbol=coin.get('symbol', '').upper(),
                            name=coin.get('name', ''),
                            price=float(quote.get('price', 0)),
                            market_cap=float(quote.get('market_cap', 0)) if quote.get('market_cap') else None,
                            volume_24h=float(quote.get('volume_24h', 0)) if quote.get('volume_24h') else None,
                            percent_change_1h=float(quote.get('percent_change_1h', 0)) if quote.get('percent_change_1h') is not None else None,
                            percent_change_24h=float(quote.get('percent_change_24h', 0)) if quote.get('percent_change_24h') is not None else None,
                            percent_change_7d=float(quote.get('percent_change_7d', 0)) if quote.get('percent_change_7d') is not None else None,
                            circulating_supply=float(coin.get('circulating_supply', 0)) if coin.get('circulating_supply') else None,
                            total_supply=float(coin.get('total_supply', 0)) if coin.get('total_supply') else None,
                            max_supply=float(coin.get('max_supply', 0)) if coin.get('max_supply') else None,
                            rank=int(coin.get('cmc_rank', 0)) if coin.get('cmc_rank') else None
                        )
                        price_items.append(price_data)

                    logger.info(f"Scraped {len(listings)} top coin prices from CoinMarketCap")

            except Exception as e:
                logger.error(f"CoinMarketCap scraping failed: {e}")
                self.stats['total_errors'] += 1
        else:
            logger.warning("CoinMarketCap API key not configured, skipping CoinMarketCap scraping")

        total_scraped = len(news_items) + len(price_items)
        self.stats['total_scraped'] += total_scraped

        return {
            'news': news_items,
            'prices': price_items
        }

    async def run_scrape_cycle(self):
        """Execute one complete scrape cycle"""
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("Starting crypto scrape cycle")

        try:
            # Scrape from all sources
            scraped_data = await self.scrape_all_sources()
            news_items = scraped_data['news']
            price_items = scraped_data['prices']

            if not news_items and not price_items:
                logger.warning("No items scraped from any source")
                return

            total_success = 0
            total_errors = 0

            # Publish news to crypto-news topic
            if news_items:
                success, errors = self.kafka_publisher.publish_batch(news_items, 'crypto-news')
                total_success += success
                total_errors += errors
                logger.info(f"Published {success} news articles to crypto-news topic")

            # Publish prices to crypto-prices topic
            if price_items:
                success, errors = self.kafka_publisher.publish_batch(price_items, 'crypto-prices')
                total_success += success
                total_errors += errors
                logger.info(f"Published {success} price updates to crypto-prices topic")

            self.stats['total_published'] += total_success
            self.stats['total_errors'] += total_errors

            # Update stats
            self.stats['last_scrape_time'] = datetime.utcnow().isoformat()
            elapsed_time = time.time() - start_time

            logger.info(f"Scrape cycle completed in {elapsed_time:.2f}s")
            logger.info(f"Scraped: {len(news_items)} news + {len(price_items)} prices, Published: {total_success}, Errors: {total_errors}")
            logger.info(f"Total stats - Scraped: {self.stats['total_scraped']}, Published: {self.stats['total_published']}, Errors: {self.stats['total_errors']}")

        except Exception as e:
            logger.error(f"Scrape cycle failed: {e}", exc_info=True)
            self.stats['total_errors'] += 1

    async def run_forever(self):
        """Run scraper continuously with configured interval"""
        logger.info(f"Starting crypto news scraper (interval: {self.scrape_interval}s)")
        logger.info(f"Kafka: {self.kafka_publisher.bootstrap_servers}")
        logger.info(f"NewsAPI: {'Enabled' if self.newsapi_key else 'Disabled'}")
        logger.info(f"CoinMarketCap: {'Enabled' if self.coinmarketcap_api_key else 'Disabled'}")

        while True:
            try:
                await self.run_scrape_cycle()
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}", exc_info=True)

            # Wait for next cycle
            logger.info(f"Sleeping for {self.scrape_interval}s until next scrape...")
            await asyncio.sleep(self.scrape_interval)

    def shutdown(self):
        """Gracefully shutdown the scraper"""
        logger.info("Shutting down crypto news scraper...")
        self.kafka_publisher.close()
        logger.info("Shutdown complete")


async def main():
    """Main entry point"""
    # Load configuration from environment variables
    kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    newsapi_key = os.getenv('NEWS_API_KEY')
    coinmarketcap_api_key = os.getenv('COINMARKETCAP_API_KEY')
    scrape_interval = int(os.getenv('SCRAPER_INTERVAL', '30'))

    # Log configuration (without sensitive data)
    logger.info("=" * 60)
    logger.info("CRYPTO VIZ - Crypto News Scraper Service")
    logger.info("=" * 60)
    logger.info(f"Kafka Bootstrap Servers: {kafka_servers}")
    logger.info(f"NewsAPI Key: {'✓ Configured' if newsapi_key else '✗ Not configured'}")
    logger.info(f"CoinMarketCap API Key: {'✓ Configured' if coinmarketcap_api_key else '✗ Not configured'}")
    logger.info(f"Scrape Interval: {scrape_interval}s")
    logger.info("=" * 60)

    # Create and run scraper
    scraper = CryptoNewsScraper(
        kafka_bootstrap_servers=kafka_servers,
        newsapi_key=newsapi_key,
        coinmarketcap_api_key=coinmarketcap_api_key,
        scrape_interval=scrape_interval
    )

    try:
        await scraper.run_forever()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        scraper.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
