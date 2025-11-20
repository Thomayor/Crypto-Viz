#!/usr/bin/env python3
"""
CRYPTO VIZ - Social Sentiment Scraper Service
Scrapes cryptocurrency mentions and sentiment from Reddit
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict

import praw
from praw.models import Submission, Comment
from kafka import KafkaProducer
from kafka.errors import KafkaError
import backoff

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Subreddits to monitor for crypto discussions
CRYPTO_SUBREDDITS = [
    'CryptoCurrency',
    'Bitcoin',
    'ethereum',
    'cardano',
    'solana',
    'polkadot',
    'CryptoMarkets',
    'altcoin',
    'defi',
    'NFT'
]


@dataclass
class SocialPost:
    """Data class for social media posts"""
    platform: str
    post_id: str
    author: str
    title: Optional[str]
    text: str
    score: int
    num_comments: int
    created_utc: str
    subreddit: str
    url: str
    coins_mentioned: List[str]
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict:
        """Convert to dictionary for Kafka serialization"""
        return {k: v for k, v in asdict(self).items() if v is not None}


class TextPreprocessor:
    """Preprocesses text for sentiment analysis"""

    # Common cryptocurrency keywords and symbols
    CRYPTO_KEYWORDS = {
        'bitcoin': 'BTC',
        'btc': 'BTC',
        'ethereum': 'ETH',
        'eth': 'ETH',
        'cardano': 'ADA',
        'ada': 'ADA',
        'solana': 'SOL',
        'sol': 'SOL',
        'polkadot': 'DOT',
        'dot': 'DOT',
        'ripple': 'XRP',
        'xrp': 'XRP',
        'dogecoin': 'DOGE',
        'doge': 'DOGE',
        'shiba': 'SHIB',
        'shib': 'SHIB',
        'polygon': 'MATIC',
        'matic': 'MATIC',
        'avalanche': 'AVAX',
        'avax': 'AVAX',
        'chainlink': 'LINK',
        'link': 'LINK',
        'cosmos': 'ATOM',
        'atom': 'ATOM',
        'litecoin': 'LTC',
        'ltc': 'LTC',
        'binance': 'BNB',
        'bnb': 'BNB'
    }

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""

        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text.strip()

    @classmethod
    def extract_coins(cls, text: str) -> List[str]:
        """Extract cryptocurrency mentions from text"""
        if not text:
            return []

        text_lower = text.lower()
        coins_found = set()

        # Check for cryptocurrency keywords
        for keyword, symbol in cls.CRYPTO_KEYWORDS.items():
            # Look for whole word matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                coins_found.add(symbol)

        # Also check for symbols with $ prefix (e.g., $BTC)
        symbol_pattern = r'\$([A-Z]{2,5})\b'
        for match in re.finditer(symbol_pattern, text):
            symbol = match.group(1)
            if symbol in cls.CRYPTO_KEYWORDS.values():
                coins_found.add(symbol)

        return sorted(list(coins_found))


class RedditRateLimiter:
    """Rate limiter for Reddit API calls"""

    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.period = 60.0  # seconds
        self.calls = []

    async def acquire(self):
        """Acquire permission to make an API call"""
        now = time.time()

        # Remove calls outside the time window
        self.calls = [call_time for call_time in self.calls
                      if call_time > now - self.period]

        if len(self.calls) >= self.calls_per_minute:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                return await self.acquire()

        self.calls.append(now)
        return True


class RedditScraper:
    """Scraper for Reddit API"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str
    ):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        self.rate_limiter = RedditRateLimiter(calls_per_minute=60)
        self.preprocessor = TextPreprocessor()
        self.seen_posts: Set[str] = set()

        logger.info("Reddit API initialized successfully")

    async def scrape_subreddit(
        self,
        subreddit_name: str,
        limit: int = 25,
        time_filter: str = 'day'
    ) -> List[SocialPost]:
        """Scrape posts from a subreddit"""
        posts = []

        try:
            await self.rate_limiter.acquire()

            subreddit = self.reddit.subreddit(subreddit_name)

            # Get hot posts from the subreddit
            for submission in subreddit.hot(limit=limit):
                # Skip if we've already seen this post
                if submission.id in self.seen_posts:
                    continue

                # Extract text content
                text = submission.selftext if submission.selftext else submission.title
                cleaned_text = self.preprocessor.clean_text(text)

                # Only include posts that mention cryptocurrencies
                coins_mentioned = self.preprocessor.extract_coins(
                    submission.title + " " + text
                )

                if not coins_mentioned:
                    continue

                # Create social post object
                post = SocialPost(
                    platform='reddit',
                    post_id=submission.id,
                    author=str(submission.author) if submission.author else '[deleted]',
                    title=submission.title,
                    text=cleaned_text[:1000],  # Limit text length
                    score=submission.score,
                    num_comments=submission.num_comments,
                    created_utc=datetime.fromtimestamp(submission.created_utc).isoformat(),
                    subreddit=subreddit_name,
                    url=f"https://reddit.com{submission.permalink}",
                    coins_mentioned=coins_mentioned
                )

                posts.append(post)
                self.seen_posts.add(submission.id)

            logger.info(f"Scraped {len(posts)} relevant posts from r/{subreddit_name}")

        except Exception as e:
            logger.error(f"Error scraping r/{subreddit_name}: {e}")

        return posts

    async def scrape_all_subreddits(
        self,
        subreddits: List[str],
        limit_per_subreddit: int = 10
    ) -> List[SocialPost]:
        """Scrape posts from multiple subreddits"""
        all_posts = []

        for subreddit in subreddits:
            try:
                posts = await self.scrape_subreddit(
                    subreddit,
                    limit=limit_per_subreddit
                )
                all_posts.extend(posts)

                # Small delay between subreddits
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Failed to scrape r/{subreddit}: {e}")

        logger.info(f"Total scraped: {len(all_posts)} posts from {len(subreddits)} subreddits")
        return all_posts


class KafkaSocialPublisher:
    """Publishes social media data to Kafka"""

    def __init__(self, bootstrap_servers: str, topic: str = 'social-posts'):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer: Optional[KafkaProducer] = None
        self._setup_producer()

    def _setup_producer(self):
        """Initialize Kafka producer"""
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
    def publish(self, post: SocialPost) -> bool:
        """Publish a single social post to Kafka"""
        try:
            key = post.post_id
            value = post.to_dict()

            future = self.producer.send(
                self.topic,
                key=key,
                value=value,
                timestamp_ms=int(time.time() * 1000)
            )

            record_metadata = future.get(timeout=10)

            logger.debug(
                f"Published to Kafka: topic={record_metadata.topic}, "
                f"partition={record_metadata.partition}, offset={record_metadata.offset}"
            )
            return True

        except KafkaError as e:
            logger.error(f"Failed to publish to Kafka: {e}")
            raise

    def publish_batch(self, posts: List[SocialPost]) -> tuple[int, int]:
        """Publish multiple posts to Kafka"""
        success_count = 0
        error_count = 0

        for post in posts:
            try:
                self.publish(post)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to publish post {post.post_id}: {e}")
                error_count += 1

        logger.info(f"Published {success_count}/{len(posts)} posts to {self.topic} (errors: {error_count})")
        return success_count, error_count

    def close(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")


class SocialSentimentScraper:
    """Main orchestrator for social sentiment scraping"""

    def __init__(
        self,
        reddit_client_id: str,
        reddit_client_secret: str,
        reddit_user_agent: str,
        kafka_bootstrap_servers: str,
        scrape_interval: int = 600,  # 10 minutes
        subreddits: List[str] = None
    ):
        self.reddit_scraper = RedditScraper(
            client_id=reddit_client_id,
            client_secret=reddit_client_secret,
            user_agent=reddit_user_agent
        )
        self.kafka_publisher = KafkaSocialPublisher(kafka_bootstrap_servers)
        self.scrape_interval = scrape_interval
        self.subreddits = subreddits or CRYPTO_SUBREDDITS

        self.stats = {
            'total_scraped': 0,
            'total_published': 0,
            'total_errors': 0,
            'last_scrape_time': None
        }

    async def run_scrape_cycle(self):
        """Execute one complete scrape cycle"""
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("Starting social sentiment scrape cycle")

        try:
            # Scrape from all subreddits
            posts = await self.reddit_scraper.scrape_all_subreddits(
                self.subreddits,
                limit_per_subreddit=10
            )

            if not posts:
                logger.warning("No relevant posts found")
                return

            # Publish to Kafka
            success_count, error_count = self.kafka_publisher.publish_batch(posts)
            self.stats['total_scraped'] += len(posts)
            self.stats['total_published'] += success_count
            self.stats['total_errors'] += error_count

            # Update stats
            self.stats['last_scrape_time'] = datetime.utcnow().isoformat()
            elapsed_time = time.time() - start_time

            logger.info(f"Scrape cycle completed in {elapsed_time:.2f}s")
            logger.info(f"Scraped: {len(posts)}, Published: {success_count}, Errors: {error_count}")
            logger.info(f"Total stats - Scraped: {self.stats['total_scraped']}, "
                       f"Published: {self.stats['total_published']}, "
                       f"Errors: {self.stats['total_errors']}")

        except Exception as e:
            logger.error(f"Scrape cycle failed: {e}", exc_info=True)
            self.stats['total_errors'] += 1

    async def run_forever(self):
        """Run scraper continuously"""
        logger.info(f"Starting social sentiment scraper (interval: {self.scrape_interval}s)")
        logger.info(f"Kafka: {self.kafka_publisher.bootstrap_servers}")
        logger.info(f"Monitoring {len(self.subreddits)} subreddits: {', '.join(self.subreddits[:5])}...")
        logger.info("=" * 60)

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
        logger.info("Shutting down social sentiment scraper...")
        self.kafka_publisher.close()
        logger.info("Shutdown complete")


async def main():
    """Main entry point"""
    # Load configuration from environment variables
    kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
    reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    reddit_user_agent = os.getenv('REDDIT_USER_AGENT', 'CryptoViz/1.0')
    scrape_interval = int(os.getenv('SOCIAL_SCRAPER_INTERVAL', '600'))

    # Validate required credentials
    if not reddit_client_id or not reddit_client_secret:
        logger.error("Reddit API credentials not configured!")
        logger.error("Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables")
        return

    # Log configuration
    logger.info("=" * 60)
    logger.info("CRYPTO VIZ - Social Sentiment Scraper Service")
    logger.info("=" * 60)
    logger.info(f"Kafka Bootstrap Servers: {kafka_servers}")
    logger.info(f"Reddit Client ID: {'✓ Configured' if reddit_client_id else '✗ Not configured'}")
    logger.info(f"Reddit Client Secret: {'✓ Configured' if reddit_client_secret else '✗ Not configured'}")
    logger.info(f"Scrape Interval: {scrape_interval}s ({scrape_interval//60} minutes)")
    logger.info(f"Subreddits: {len(CRYPTO_SUBREDDITS)}")
    logger.info("=" * 60)

    # Create and run scraper
    scraper = SocialSentimentScraper(
        reddit_client_id=reddit_client_id,
        reddit_client_secret=reddit_client_secret,
        reddit_user_agent=reddit_user_agent,
        kafka_bootstrap_servers=kafka_servers,
        scrape_interval=scrape_interval
    )

    try:
        await scraper.run_forever()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    finally:
        scraper.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
