"""
CRYPTO VIZ - Kafka Consumer Service
Consumes messages from Kafka topics and broadcasts to WebSocket clients
"""

import os
import json
import logging
import asyncio
from typing import Optional, Callable
from kafka import KafkaConsumer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class KafkaConsumerService:
    """Service for consuming Kafka messages and broadcasting to WebSocket"""

    def __init__(self, bootstrap_servers: str = None):
        """
        Initialize Kafka consumer service

        Args:
            bootstrap_servers: Kafka bootstrap servers (default from env)
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
        self.consumers = {}
        self.consumer_tasks = {}
        self.running = False

    def create_consumer(self, topic: str, group_id: str) -> Optional[KafkaConsumer]:
        """
        Create a Kafka consumer for a specific topic

        Args:
            topic: Kafka topic name
            group_id: Consumer group ID

        Returns:
            KafkaConsumer instance or None if failed
        """
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,
                auto_offset_reset='latest',  # Start from latest messages
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
                consumer_timeout_ms=1000,  # Timeout for polling
                api_version=(2, 5, 0)
            )
            logger.info(f"✓ Kafka consumer created for topic '{topic}' (group: {group_id})")
            return consumer

        except KafkaError as e:
            logger.error(f"Failed to create Kafka consumer for topic '{topic}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating Kafka consumer: {e}")
            return None

    async def start_consuming(self, topic: str, callback: Callable, group_id: str = None):
        """
        Start consuming messages from a Kafka topic

        Args:
            topic: Kafka topic to consume from
            callback: Async callback function to handle messages
            group_id: Consumer group ID (default: topic-based)
        """
        if topic in self.consumer_tasks and not self.consumer_tasks[topic].done():
            logger.warning(f"Consumer for topic '{topic}' is already running")
            return

        group_id = group_id or f"websocket-{topic}-consumer"

        # Create consumer in thread pool (Kafka consumer is not async)
        loop = asyncio.get_event_loop()
        consumer = await loop.run_in_executor(None, self.create_consumer, topic, group_id)

        if not consumer:
            logger.error(f"Failed to start consumer for topic '{topic}'")
            return

        self.consumers[topic] = consumer

        # Start consumer task
        task = asyncio.create_task(self._consume_loop(topic, consumer, callback))
        self.consumer_tasks[topic] = task

        logger.info(f"Started consuming from topic '{topic}'")

    async def _consume_loop(self, topic: str, consumer: KafkaConsumer, callback: Callable):
        """
        Main consumer loop

        Args:
            topic: Topic name
            consumer: KafkaConsumer instance
            callback: Callback function for messages
        """
        logger.info(f"Consumer loop started for topic '{topic}'")
        loop = asyncio.get_event_loop()

        try:
            while self.running:
                # Poll messages in thread pool
                messages = await loop.run_in_executor(
                    None,
                    lambda: list(consumer.poll(timeout_ms=1000).values())
                )

                # Process messages
                for message_batch in messages:
                    for message in message_batch:
                        try:
                            # Call callback with message data
                            if message.value:
                                await callback(message.value)

                        except Exception as e:
                            logger.error(f"Error processing message from '{topic}': {e}")

                # Small sleep to prevent tight loop
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            logger.info(f"Consumer loop cancelled for topic '{topic}'")
        except Exception as e:
            logger.error(f"Error in consumer loop for topic '{topic}': {e}")
        finally:
            # Close consumer
            try:
                await loop.run_in_executor(None, consumer.close)
                logger.info(f"Consumer closed for topic '{topic}'")
            except Exception as e:
                logger.error(f"Error closing consumer for topic '{topic}': {e}")

    async def stop_consuming(self, topic: str = None):
        """
        Stop consuming from a topic or all topics

        Args:
            topic: Specific topic to stop (None = stop all)
        """
        topics_to_stop = [topic] if topic else list(self.consumer_tasks.keys())

        for t in topics_to_stop:
            if t in self.consumer_tasks:
                task = self.consumer_tasks[t]
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                del self.consumer_tasks[t]

            if t in self.consumers:
                del self.consumers[t]

            logger.info(f"Stopped consuming from topic '{t}'")

    async def start_all_consumers(self, websocket_manager):
        """
        Start all consumers for crypto data

        Args:
            websocket_manager: WebSocket manager instance for broadcasting
        """
        self.running = True

        # Define topics and their callbacks
        topics_config = [
            {
                "topic": "crypto-prices",
                "callback": websocket_manager.broadcast_price_update,
                "group_id": "websocket-prices-consumer"
            },
            {
                "topic": "crypto-news",
                "callback": websocket_manager.broadcast_news_update,
                "group_id": "websocket-news-consumer"
            },
            {
                "topic": "analytics-data",
                "callback": websocket_manager.broadcast_analytics_update,
                "group_id": "websocket-analytics-consumer"
            }
        ]

        # Start all consumers
        for config in topics_config:
            try:
                await self.start_consuming(
                    topic=config["topic"],
                    callback=config["callback"],
                    group_id=config["group_id"]
                )
            except Exception as e:
                logger.error(f"Failed to start consumer for {config['topic']}: {e}")

        logger.info(f"✓ All Kafka consumers started ({len(topics_config)} topics)")

    async def stop_all_consumers(self):
        """Stop all running consumers"""
        self.running = False
        await self.stop_consuming()
        logger.info("All Kafka consumers stopped")

    def get_stats(self):
        """Get consumer statistics"""
        return {
            "running": self.running,
            "active_consumers": list(self.consumers.keys()),
            "consumer_count": len(self.consumers)
        }


# Global consumer service instance
_consumer_instance: Optional[KafkaConsumerService] = None


def get_kafka_consumer() -> KafkaConsumerService:
    """Get or create global Kafka consumer service instance"""
    global _consumer_instance
    if _consumer_instance is None:
        _consumer_instance = KafkaConsumerService()
    return _consumer_instance


async def close_kafka_consumer():
    """Close Kafka consumer service"""
    global _consumer_instance
    if _consumer_instance:
        await _consumer_instance.stop_all_consumers()
        _consumer_instance = None
        logger.info("Kafka consumer service closed")
