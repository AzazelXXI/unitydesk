"""
Meeting WebSocket Service - Handles WebSocket connections and real-time communication for meetings

This service manages:
- WebSocket connection lifecycle
- Room management
- Real-time message broadcasting
- Audio/video state management
"""

from fastapi.websockets import WebSocket
from typing import Dict, Set
import logging

logger = logging.getLogger(__name__)


class SignalManager:
    """Manages WebSocket connections and signaling for a single meeting room"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # client_id -> websocket
        self.audio_state: Dict[str, bool] = (
            {}
        )  # Track audio state for each client (enabled/disabled)

    @property
    def is_empty(self):
        return len(self.active_connections) == 0

    async def connect(self, client_id: str, websocket: WebSocket):
        """Add a new WebSocket connection to the room"""
        try:
            await websocket.accept()
            self.active_connections[client_id] = websocket
            self.audio_state[client_id] = True  # Default audio to enabled
            logger.info(
                f"New connection added. Total connections: {len(self.active_connections)}"
            )
        except Exception as e:
            logger.error(f"Error connecting websocket: {e}")
            raise

    async def disconnect(self, client_id: str):
        """Remove a WebSocket connection from the room"""
        try:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
                # Clean up audio state
                if client_id in self.audio_state:
                    del self.audio_state[client_id]
                logger.info(
                    f"Connection removed. Total connections: {len(self.active_connections)}"
                )
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    async def broadcast(self, message: dict, sender_id: str):
        """Broadcast a message to all clients in the room (except sender)"""
        logger.debug(
            f"Broadcasting message type: {message.get('type')} from {sender_id}"
        )
        disconnected = set()

        # Handle audio toggle messages
        if message.get("type") == "AUDIO_TOGGLE":
            # Update sender's audio state
            is_enabled = message.get("enabled", False)
            self.audio_state[sender_id] = is_enabled
            logger.debug(
                f"Client {sender_id} audio state changed to: {'enabled' if is_enabled else 'disabled'}"
            )

        # Handle targeted messages
        if "target" in message:
            target_id = message["target"]
            if target_id in self.active_connections:
                try:
                    message["source"] = sender_id
                    # Include audio state for audio-related messages
                    if message.get("type") in ["JOIN", "OFFER", "ANSWER"]:
                        message["audioEnabled"] = self.audio_state.get(sender_id, True)
                    await self.active_connections[target_id].send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to target {target_id}: {e}")
                    disconnected.add(target_id)
            return

        # Broadcast to all except sender
        for client_id, connection in self.active_connections.items():
            if client_id != sender_id:
                try:
                    # Add source to message
                    message["source"] = sender_id
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    disconnected.add(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            await self.disconnect(client_id)


class MeetingWebSocketService:
    """Service for managing WebSocket connections across multiple meeting rooms"""

    def __init__(self):
        self.rooms: Dict[str, SignalManager] = {}

    async def join_room(self, room_id: str, client_id: str, websocket: WebSocket):
        """Add a client to a meeting room"""
        if not room_id:
            raise ValueError("Room ID cannot be empty")

        logger.info(f"Client {client_id} joining room: {room_id}")
        try:
            if room_id not in self.rooms:
                self.rooms[room_id] = SignalManager()

            await self.rooms[room_id].connect(client_id, websocket)
            logger.info(f"Join successful for client {client_id} in room {room_id}")
        except Exception as e:
            logger.error(f"Error joining room {room_id}: {e}")
            raise

    async def leave_room(self, room_id: str, client_id: str):
        """Remove a client from a meeting room"""
        if room_id in self.rooms:
            await self.rooms[room_id].disconnect(client_id)
            # Notify others about the leave
            await self.broadcast_to_room(
                room_id, {"type": "LEAVE", "clientId": client_id}, client_id
            )

            if self.rooms[room_id].is_empty:
                logger.info(f"Room {room_id} is empty, removing")
                del self.rooms[room_id]

    async def broadcast_to_room(self, room_id: str, message: dict, sender_id: str):
        """Broadcast a message to all clients in a specific room"""
        if not room_id:
            raise ValueError("Room ID cannot be empty")

        if room_id in self.rooms:
            logger.debug(f"Broadcasting in room {room_id}")
            await self.rooms[room_id].broadcast(message, sender_id)
        else:
            logger.warning(f"Attempted to broadcast to non-existent room {room_id}")

    def get_room_info(self, room_id: str) -> dict:
        """Get information about a specific room"""
        if room_id not in self.rooms:
            return {"exists": False, "participant_count": 0}

        room = self.rooms[room_id]
        return {
            "exists": True,
            "participant_count": len(room.active_connections),
            "participants": list(room.active_connections.keys()),
            "audio_states": room.audio_state.copy(),
        }

    def get_all_rooms_info(self) -> dict:
        """Get information about all active rooms"""
        return {room_id: self.get_room_info(room_id) for room_id in self.rooms.keys()}


# Global instance
meeting_websocket_service = MeetingWebSocketService()
