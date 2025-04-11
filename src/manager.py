from fastapi.websockets import WebSocket
from typing import Dict

class SignalManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    @property
    def is_empty(self):
        return len(self.active_connections) == 0

    async def connect(self, websocket: WebSocket):
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            print(f"New connection added. Total connections: {len(self.active_connections)}")
        except Exception as e:
            print(f"Error connecting websocket: {e}")
            raise

    async def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
            print(f"Connection removed. Total connections: {len(self.active_connections)}")
        except ValueError:
            print(f"Warning: Attempted to remove non-existent websocket")
        except Exception as e:
            print(f"Error during disconnect: {e}")

    async def broadcast(self, message: dict, sender: WebSocket):
        print(f"Broadcasting message type: {message.get('type')} to {len(self.active_connections)-1} peers")
        disconnected = []
        
        for connection in self.active_connections:
            if connection != sender:  # Don't send back to sender
                try:
                    await connection.send_json(message)
                    print(f"Message sent successfully to peer")
                except Exception as e:
                    print(f"Error sending to peer: {e}")
                    disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            await self.disconnect(conn)


class MeetingManager:
    def __init__(self) -> None:
        self.rooms: Dict[str, SignalManager] = {}

    async def join(self, id: str, websocket: WebSocket):
        if not id:
            raise ValueError("Room ID cannot be empty")
        
        print(f"Client joining room: {id}")
        try:
            if id not in self.rooms:
                self.rooms[id] = SignalManager()
            
            await self.rooms[id].connect(websocket)
            # Notify others in the room
            await self.broadcast(id, {"type": "USER_JOIN"}, websocket)
            print(f"Join successful, notified peers in room {id}")
        except Exception as e:
            print(f"Error joining room {id}: {e}")
            raise

    async def leave(self, id: str, websocket: WebSocket):
        if id in self.rooms:
            await self.rooms[id].disconnect(websocket)
            if self.rooms[id].is_empty:
                print(f"Room {id} is empty, removing")
                del self.rooms[id]

    async def broadcast(self, room_id: str, message: dict, websocket: WebSocket):
        if not room_id:
            raise ValueError("Room ID cannot be empty")
            
        if room_id in self.rooms:
            print(f"Broadcasting to room {room_id}")
            await self.rooms[room_id].broadcast(message, websocket)
        else:
            print(f"Warning: Attempted to broadcast to non-existent room {room_id}")
