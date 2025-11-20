"""
CRYPTO VIZ - WebSocket Manager
Manages WebSocket connections and broadcasts messages
"""

import logging
import json
import asyncio
from typing import Set, Dict, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""

    def __init__(self):
        """Initialize connection manager"""
        self.active_connections: Set[WebSocket] = set()
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        self._heartbeat_task = None
        self._heartbeat_interval = 30  # seconds

    async def connect(self, websocket: WebSocket, client_id: str = None):
        """
        Accept and register a new WebSocket connection

        Args:
            websocket: WebSocket connection
            client_id: Optional client identifier
        """
        await websocket.accept()
        self.active_connections.add(websocket)

        # Store connection metadata
        self.connection_metadata[websocket] = {
            "client_id": client_id or f"client_{id(websocket)}",
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }

        logger.info(f"WebSocket client connected: {self.connection_metadata[websocket]['client_id']} "
                   f"(Total connections: {len(self.active_connections)})")

        # Send welcome message
        await self.send_personal_message({
            "type": "connection",
            "status": "connected",
            "client_id": self.connection_metadata[websocket]['client_id'],
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection

        Args:
            websocket: WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

            client_id = self.connection_metadata.get(websocket, {}).get("client_id", "unknown")
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]

            logger.info(f"WebSocket client disconnected: {client_id} "
                       f"(Remaining connections: {len(self.active_connections)})")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """
        Send message to a specific client

        Args:
            message: Message data
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any], message_type: str = None):
        """
        Broadcast message to all connected clients

        Args:
            message: Message data to broadcast
            message_type: Type of message for logging
        """
        if not self.active_connections:
            return

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                disconnected.add(connection)
                logger.warning(f"Client disconnected during broadcast")
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

        if message_type:
            logger.debug(f"Broadcast {message_type} to {len(self.active_connections)} clients")

    async def broadcast_price_update(self, price_data: Dict[str, Any]):
        """
        Broadcast cryptocurrency price update

        Args:
            price_data: Price update data from Kafka
        """
        message = {
            "type": "price_update",
            "data": {
                "symbol": price_data.get("symbol"),
                "price": float(price_data.get("price", 0)),
                "price_change_24h": float(price_data.get("percent_change_24h", 0)) if price_data.get("percent_change_24h") else None,
                "volume_24h": float(price_data.get("volume_24h", 0)) if price_data.get("volume_24h") else None,
                "market_cap": float(price_data.get("market_cap", 0)) if price_data.get("market_cap") else None,
                "rank": price_data.get("rank"),
                "timestamp": price_data.get("timestamp", datetime.utcnow().isoformat())
            }
        }
        await self.broadcast(message, "price_update")

    async def broadcast_news_update(self, news_data: Dict[str, Any]):
        """
        Broadcast cryptocurrency news update

        Args:
            news_data: News data from Kafka
        """
        message = {
            "type": "news_update",
            "data": {
                "title": news_data.get("title"),
                "description": news_data.get("description"),
                "url": news_data.get("url"),
                "source": news_data.get("source"),
                "published_at": news_data.get("published_at"),
                "sentiment_score": news_data.get("sentiment_score"),
                "sentiment_label": news_data.get("sentiment_label"),
                "mentioned_coins": news_data.get("mentioned_coins", []),
                "timestamp": news_data.get("timestamp", datetime.utcnow().isoformat())
            }
        }
        await self.broadcast(message, "news_update")

    async def broadcast_analytics_update(self, analytics_data: Dict[str, Any]):
        """
        Broadcast analytics update

        Args:
            analytics_data: Analytics data from Kafka
        """
        message = {
            "type": "analytics_update",
            "data": analytics_data
        }
        await self.broadcast(message, "analytics_update")

    async def start_heartbeat(self):
        """Start heartbeat task to keep connections alive"""
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            logger.info("WebSocket heartbeat started")

    async def stop_heartbeat(self):
        """Stop heartbeat task"""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            logger.info("WebSocket heartbeat stopped")

    async def _heartbeat_loop(self):
        """Heartbeat loop to send ping messages"""
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)

                if self.active_connections:
                    ping_message = {
                        "type": "ping",
                        "timestamp": datetime.utcnow().isoformat()
                    }

                    disconnected = set()
                    for connection in self.active_connections:
                        try:
                            await connection.send_json(ping_message)
                            # Update last ping time
                            if connection in self.connection_metadata:
                                self.connection_metadata[connection]["last_ping"] = datetime.utcnow()
                        except Exception as e:
                            logger.warning(f"Heartbeat failed for client: {e}")
                            disconnected.add(connection)

                    # Clean up failed connections
                    for connection in disconnected:
                        self.disconnect(connection)

                    if disconnected:
                        logger.info(f"Cleaned up {len(disconnected)} failed connections")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics

        Returns:
            Dictionary with connection stats
        """
        return {
            "active_connections": len(self.active_connections),
            "clients": [
                {
                    "client_id": meta["client_id"],
                    "connected_at": meta["connected_at"].isoformat(),
                    "last_ping": meta["last_ping"].isoformat()
                }
                for meta in self.connection_metadata.values()
            ]
        }


# Global connection manager instance
_manager_instance: ConnectionManager = None


def get_manager() -> ConnectionManager:
    """Get or create global connection manager instance"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ConnectionManager()
    return _manager_instance


async def close_manager():
    """Close all connections and cleanup"""
    global _manager_instance
    if _manager_instance:
        await _manager_instance.stop_heartbeat()
        # Close all active connections
        for connection in list(_manager_instance.active_connections):
            try:
                await connection.close()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
        _manager_instance = None
        logger.info("WebSocket manager closed")
