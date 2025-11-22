# app/websocket_manager.py

from fastapi import WebSocket
from typing import Dict, List
import uuid

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict] = {}  # player_id -> {"websocket": ..., "chat_id": ...}
        self.player_counter = 0  # For assigning Player 1, Player 2, etc.

    async def connect(self, websocket: WebSocket):
        """Assign a Chat ID and register player connection."""
        await websocket.accept()
        self.player_counter += 1
        player_id = str(uuid.uuid4())
        chat_id = f"Player {self.player_counter}"

        self.active_connections[player_id] = {
            "websocket": websocket,
            "chat_id": chat_id
        }
        return player_id, chat_id

    def disconnect(self, player_id: str):
        """Remove player from active connections."""
        if player_id in self.active_connections:
            del self.active_connections[player_id]

    async def send_personal_message(self, message: str, player_id: str):
        """Send a private message to a specific player."""
        player = self.active_connections.get(player_id)
        if player and player["websocket"]:
            await player["websocket"].send_text(message)

    async def broadcast(self, message: str):
        """Broadcast message to all human players."""
        for player in self.active_connections.values():
            if player["websocket"]:
                await player["websocket"].send_text(message)

    def get_active_players(self) -> List[Dict]:
        """Return list of all players' Chat IDs (including AI)."""
        return [
            {"chat_id": pdata["chat_id"]}
            for pdata in self.active_connections.values()
        ]

    def get_human_player_count(self) -> int:
        """Count only human players (with active WebSockets)."""
        return len([p for p in self.active_connections.values() if p["websocket"]])

    def register_ai_bot(self):
        """Register AI bot as a Player with no WebSocket."""
        self.player_counter += 1
        ai_id = "AI-" + str(uuid.uuid4())
        chat_id = f"Player {self.player_counter}"

        self.active_connections[ai_id] = {
            "websocket": None,   # AI bot doesn't have a WebSocket
            "chat_id": chat_id
        }
        return ai_id, chat_id
    
    def list_all_players(self):
        return [player["chat_id"] for player in self.active_connections.values()]

    def active_player_count(self):
        return len([p for p in self.active_connections.values() if p["websocket"] is not None])


manager = ConnectionManager()