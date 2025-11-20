"""
CRYPTO VIZ - WebSocket Router
Real-time data streaming via WebSocket
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional

from services.websocket_manager import get_manager
from services.kafka_consumer import get_kafka_consumer

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

# Get global managers
websocket_manager = get_manager()
kafka_consumer = get_kafka_consumer()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(default=None, description="Client identifier")
):
    """
    WebSocket endpoint for real-time crypto data streaming

    **Connection URL**: `ws://localhost:8000/ws?client_id=your_id`

    **Message Types**:
    - `connection`: Connection established
    - `ping`: Heartbeat message (every 30s)
    - `price_update`: Real-time price updates from crypto-prices topic
    - `news_update`: Real-time news from crypto-news topic
    - `analytics_update`: Real-time analytics from analytics-data topic

    **Example Messages**:

    Price Update:
    ```json
    {
      "type": "price_update",
      "data": {
        "symbol": "BTC",
        "price": 45000.0,
        "price_change_24h": 2.5,
        "volume_24h": 1000000000.0,
        "market_cap": 850000000000.0,
        "rank": 1,
        "timestamp": "2024-01-01T12:00:00Z"
      }
    }
    ```

    News Update:
    ```json
    {
      "type": "news_update",
      "data": {
        "title": "Bitcoin reaches new high",
        "description": "Bitcoin surpassed $50k...",
        "url": "https://...",
        "source": "CoinDesk",
        "published_at": "2024-01-01T12:00:00Z",
        "sentiment_score": 0.85,
        "sentiment_label": "positive",
        "mentioned_coins": ["BTC"],
        "timestamp": "2024-01-01T12:00:00Z"
      }
    }
    ```

    Analytics Update:
    ```json
    {
      "type": "analytics_update",
      "data": {
        "symbol": "BTC",
        "metric_type": "volatility",
        "metric_value": 0.035,
        "calculated_at": "2024-01-01T12:00:00Z",
        "timestamp": "2024-01-01T12:00:00Z"
      }
    }
    ```

    **Reconnection**: Client should implement automatic reconnection with exponential backoff
    """
    # Connect client
    await websocket_manager.connect(websocket, client_id)

    try:
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive messages from client (if any)
                data = await websocket.receive_json()

                # Handle client messages
                message_type = data.get("type")

                if message_type == "pong":
                    # Client responded to ping
                    logger.debug(f"Received pong from client {client_id}")

                elif message_type == "subscribe":
                    # Client wants to subscribe to specific topics
                    topics = data.get("topics", [])
                    await websocket_manager.send_personal_message({
                        "type": "subscription",
                        "status": "acknowledged",
                        "topics": topics
                    }, websocket)

                elif message_type == "unsubscribe":
                    # Client wants to unsubscribe from topics
                    topics = data.get("topics", [])
                    await websocket_manager.send_personal_message({
                        "type": "unsubscription",
                        "status": "acknowledged",
                        "topics": topics
                    }, websocket)

                elif message_type == "stats":
                    # Client requests connection stats
                    stats = websocket_manager.get_stats()
                    await websocket_manager.send_personal_message({
                        "type": "stats",
                        "data": stats
                    }, websocket)

                else:
                    logger.warning(f"Unknown message type from client: {message_type}")

            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Disconnect client
        websocket_manager.disconnect(websocket)


@router.get("/ws/stats", summary="Get WebSocket statistics")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics

    Returns information about active WebSocket connections
    """
    ws_stats = websocket_manager.get_stats()
    kafka_stats = kafka_consumer.get_stats()

    return {
        "websocket": ws_stats,
        "kafka_consumer": kafka_stats
    }


# Startup and shutdown functions
async def start_websocket_service():
    """Start WebSocket service (called on app startup)"""
    logger.info("Starting WebSocket service...")

    # Start heartbeat
    await websocket_manager.start_heartbeat()
    logger.info("✓ WebSocket heartbeat started")

    # Start Kafka consumers
    try:
        await kafka_consumer.start_all_consumers(websocket_manager)
        logger.info("✓ Kafka consumers started")
    except Exception as e:
        logger.error(f"Failed to start Kafka consumers: {e}")
        logger.warning("WebSocket service will start without Kafka integration")

    logger.info("✓ WebSocket service started")


async def stop_websocket_service():
    """Stop WebSocket service (called on app shutdown)"""
    logger.info("Stopping WebSocket service...")

    # Stop Kafka consumers
    try:
        await kafka_consumer.stop_all_consumers()
        logger.info("✓ Kafka consumers stopped")
    except Exception as e:
        logger.error(f"Error stopping Kafka consumers: {e}")

    # Stop heartbeat
    try:
        await websocket_manager.stop_heartbeat()
        logger.info("✓ WebSocket heartbeat stopped")
    except Exception as e:
        logger.error(f"Error stopping heartbeat: {e}")

    logger.info("✓ WebSocket service stopped")
