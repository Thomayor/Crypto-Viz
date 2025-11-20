#!/usr/bin/env python3
"""
Kafka Consumer with PostgreSQL Integration
Consumes data from Kafka topics and writes to PostgreSQL
"""

import os
import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import time

from postgres_writer import PostgreSQLWriter
from ollama_sentiment_engine import OllamaSentimentEngine

logger = logging.getLogger(__name__)


class CryptoKafkaConsumer:
    """Kafka consumer that writes to PostgreSQL"""

    def __init__(self):
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
        self.group_id = os.getenv('KAFKA_GROUP_ID', 'crypto-viz-analytics')

        # Topics to consume
        self.topics = [
            'crypto-prices',
            'crypto-news',
            'social-posts'
        ]

        # PostgreSQL writer
        self.pg_writer = PostgreSQLWriter(min_conn=2, max_conn=10)

        # Sentiment analyzer
        try:
            self.sentiment_engine = OllamaSentimentEngine()
            logger.info("✓ Sentiment engine initialized")
        except Exception as e:
            logger.warning(f"Sentiment engine initialization failed: {e}")
            self.sentiment_engine = None

        # Statistics
        self.stats = {
            'crypto-prices': 0,
            'crypto-news': 0,
            'social-posts': 0,
            'errors': 0,
            'sentiment_analyzed': 0,
            'sentiment_errors': 0
        }

        # Initialize consumer
        self.consumer = None
        self._init_consumer()

    def _init_consumer(self, max_retries: int = 5) -> bool:
        """Initialize Kafka consumer with retries"""
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Initializing Kafka consumer (attempt {attempt}/{max_retries})...")

                self.consumer = KafkaConsumer(
                    *self.topics,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=self.group_id,
                    auto_offset_reset='latest',
                    enable_auto_commit=True,
                    auto_commit_interval_ms=5000,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    max_poll_records=100,
                    session_timeout_ms=30000,
                    request_timeout_ms=40000
                )

                logger.info(f"✓ Kafka consumer initialized successfully")
                logger.info(f"Subscribed to topics: {', '.join(self.topics)}")
                return True

            except Exception as e:
                logger.error(f"Failed to initialize Kafka consumer: {e}")
                if attempt < max_retries:
                    wait_time = 5 * attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("Failed to initialize Kafka consumer after all retries")
                    raise

        return False

    def process_crypto_price(self, message: Dict[str, Any]) -> bool:
        """Process and store crypto price data"""
        try:
            # Extract required fields
            price_data = {
                'symbol': message.get('symbol', '').upper(),
                'name': message.get('name', ''),
                'price': float(message.get('price', 0)),
                'market_cap': float(message.get('market_cap', 0)) if message.get('market_cap') else None,
                'volume_24h': float(message.get('volume_24h', 0)) if message.get('volume_24h') else None,
                'percent_change_1h': float(message.get('percent_change_1h', 0)) if message.get('percent_change_1h') else None,
                'percent_change_24h': float(message.get('percent_change_24h', 0)) if message.get('percent_change_24h') else None,
                'percent_change_7d': float(message.get('percent_change_7d', 0)) if message.get('percent_change_7d') else None,
                'circulating_supply': float(message.get('circulating_supply', 0)) if message.get('circulating_supply') else None,
                'total_supply': float(message.get('total_supply', 0)) if message.get('total_supply') else None,
                'max_supply': float(message.get('max_supply', 0)) if message.get('max_supply') else None,
                'rank': int(message.get('rank', 0)) if message.get('rank') else None,
                'timestamp': datetime.fromisoformat(message['timestamp']) if 'timestamp' in message else datetime.now()
            }

            # Write to PostgreSQL
            if self.pg_writer.write_crypto_price(price_data):
                self.stats['crypto-prices'] += 1
                return True

            return False

        except Exception as e:
            logger.error(f"Error processing crypto price: {e}")
            self.stats['errors'] += 1
            return False

    def process_crypto_news(self, message: Dict[str, Any]) -> bool:
        """Process and store crypto news data"""
        try:
            # Analyze sentiment if engine available
            sentiment_score = None
            sentiment_label = None
            analysis_method = 'lexicon'  # Default fallback method
            confidence_score = None
            keywords = message.get('keywords', [])

            if self.sentiment_engine:
                try:
                    # Combine title and description for analysis
                    text = f"{message.get('title', '')} {message.get('description', '')}"
                    logger.info(f"[KAFKA DEBUG] About to analyze news text (len={len(text)}): {text[:100]}")
                    if text.strip():
                        logger.info(f"[KAFKA DEBUG] Calling sentiment_engine.analyze_text...")
                        sentiment_result = self.sentiment_engine.analyze_text(
                            text=text,
                            source_type='news',
                            metadata={'url': message.get('url')}
                        )
                        logger.info(f"[KAFKA DEBUG] analyze_text returned: {type(sentiment_result)}, value: {sentiment_result}")

                        sentiment_score = sentiment_result['sentiment_score']
                        sentiment_label = sentiment_result['sentiment_label']
                        analysis_method = sentiment_result.get('method', 'lexicon')
                        confidence_score = sentiment_result.get('confidence')
                        logger.info(f"[KAFKA DEBUG] Extracted score={sentiment_score}, label={sentiment_label}, method={analysis_method}, confidence={confidence_score}")

                        # Merge keywords if not already present
                        if sentiment_result.get('keywords'):
                            keywords = list(set(keywords + sentiment_result['keywords']))

                        self.stats['sentiment_analyzed'] += 1
                        logger.debug(
                            f"Sentiment: {sentiment_label} ({sentiment_score:.2f}) "
                            f"via {sentiment_result.get('method', 'unknown')}"
                        )

                except Exception as e:
                    logger.warning(f"Sentiment analysis failed for news: {e}")
                    self.stats['sentiment_errors'] += 1

            # Extract required fields with sentiment
            news_data = {
                'source': message.get('source', ''),
                'author': message.get('author'),
                'title': message.get('title', ''),
                'description': message.get('description'),
                'url': message.get('url', ''),
                'url_to_image': message.get('urlToImage'),
                'content': message.get('content'),
                'published_at': datetime.fromisoformat(message['publishedAt']) if 'publishedAt' in message else datetime.now(),
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label,
                'analysis_method': analysis_method,
                'confidence_score': confidence_score,
                'keywords': keywords,
                'mentioned_coins': message.get('mentioned_coins', [])
            }

            # Write to PostgreSQL
            if self.pg_writer.write_crypto_news(news_data):
                self.stats['crypto-news'] += 1
                return True

            return False

        except Exception as e:
            logger.error(f"Error processing crypto news: {e}")
            self.stats['errors'] += 1
            return False

    def process_social_post(self, message: Dict[str, Any]) -> bool:
        """Process and store social media post"""
        try:
            # Analyze sentiment if engine available
            sentiment_score = None
            sentiment_label = None

            if self.sentiment_engine:
                try:
                    # Combine title and content for analysis
                    text = f"{message.get('title', '')} {message.get('content', message.get('selftext', ''))}"
                    if text.strip():
                        sentiment_result = self.sentiment_engine.analyze_text(
                            text=text,
                            source_type='social',
                            metadata={'platform': message.get('platform', 'reddit')}
                        )

                        sentiment_score = sentiment_result['sentiment_score']
                        sentiment_label = sentiment_result['sentiment_label']

                        self.stats['sentiment_analyzed'] += 1
                        logger.debug(
                            f"Sentiment: {sentiment_label} ({sentiment_score:.2f}) "
                            f"via {sentiment_result.get('method', 'unknown')}"
                        )

                except Exception as e:
                    logger.warning(f"Sentiment analysis failed for social post: {e}")
                    self.stats['sentiment_errors'] += 1

            # Extract required fields with sentiment
            post_data = {
                'platform': message.get('platform', 'reddit'),
                'post_id': message.get('post_id', message.get('id', '')),
                'subreddit': message.get('subreddit'),
                'author': message.get('author'),
                'title': message.get('title'),
                'content': message.get('content', message.get('selftext')),
                'url': message.get('url'),
                'score': int(message.get('score', 0)) if message.get('score') else None,
                'num_comments': int(message.get('num_comments', 0)) if message.get('num_comments') else None,
                'upvote_ratio': float(message.get('upvote_ratio', 0)) if message.get('upvote_ratio') else None,
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label,
                'mentioned_coins': message.get('mentioned_coins', []),
                'published_at': datetime.fromtimestamp(float(message['created_utc'])) if 'created_utc' in message else datetime.now()
            }

            # Write to PostgreSQL
            if self.pg_writer.write_social_post(post_data):
                self.stats['social-posts'] += 1
                return True

            return False

        except Exception as e:
            logger.error(f"Error processing social post: {e}")
            self.stats['errors'] += 1
            return False

    def process_message(self, topic: str, message: Dict[str, Any]) -> bool:
        """Route message to appropriate processor"""
        try:
            if topic == 'crypto-prices':
                return self.process_crypto_price(message)
            elif topic == 'crypto-news':
                return self.process_crypto_news(message)
            elif topic == 'social-posts':
                return self.process_social_post(message)
            else:
                logger.warning(f"Unknown topic: {topic}")
                return False

        except Exception as e:
            logger.error(f"Error processing message from {topic}: {e}")
            self.stats['errors'] += 1
            return False

    def print_stats(self):
        """Print consumption statistics"""
        total = sum(self.stats.values()) - self.stats['errors']
        logger.info("=" * 60)
        logger.info("KAFKA CONSUMER STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Crypto Prices:  {self.stats['crypto-prices']:6d} messages")
        logger.info(f"Crypto News:    {self.stats['crypto-news']:6d} messages")
        logger.info(f"Social Posts:   {self.stats['social-posts']:6d} messages")
        logger.info(f"Errors:         {self.stats['errors']:6d} messages")
        logger.info(f"Total Processed: {total:6d} messages")
        logger.info("=" * 60)

    def consume(self):
        """Main consumption loop"""
        logger.info("Starting Kafka consumer loop...")
        logger.info(f"Consuming from: {', '.join(self.topics)}")

        last_stats_time = time.time()
        stats_interval = 60  # Print stats every 60 seconds

        try:
            for message in self.consumer:
                # Process message
                self.process_message(message.topic, message.value)

                # Print stats periodically
                if time.time() - last_stats_time >= stats_interval:
                    self.print_stats()
                    last_stats_time = time.time()

        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            raise
        finally:
            self.close()

    def close(self):
        """Clean shutdown"""
        logger.info("Closing Kafka consumer and PostgreSQL connections...")

        if self.consumer:
            self.consumer.close()

        if self.pg_writer:
            self.pg_writer.close_all()

        self.print_stats()
        logger.info("Consumer closed successfully")


def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("=" * 60)
    logger.info("CRYPTO VIZ - Kafka Consumer with PostgreSQL")
    logger.info("=" * 60)

    consumer = CryptoKafkaConsumer()
    consumer.consume()


if __name__ == "__main__":
    main()
