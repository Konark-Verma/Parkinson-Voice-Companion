import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket

logger = logging.getLogger("ws_manager")

class ConnectionManager:
    def __init__(self):
        # Map user_id -> Set[WebSocket]
        self.user_connections: Dict[int, Set[WebSocket]] = {}
        # Map role -> Set[WebSocket]
        self.role_connections: Dict[str, Set[WebSocket]] = {
            "PATIENT": set(),
            "CAREGIVER": set(),
            "DOCTOR": set(),
            "ADMIN": set()
        }
        # All active sockets
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, user_id: int, role: str):
        await websocket.accept()
        self.active_connections.add(websocket)

        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)

        if role not in self.role_connections:
            self.role_connections[role] = set()
        self.role_connections[role].add(websocket)
        logger.info(f"WebSocket connected: user={user_id}, role={role}, total={len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, user_id: int, role: str):
        self.active_connections.discard(websocket)
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        if role in self.role_connections:
            self.role_connections[role].discard(websocket)
        logger.info(f"WebSocket disconnected: user={user_id}, role={role}")

    async def send_to_user(self, user_id: int, message: dict):
        if user_id in self.user_connections:
            dead_sockets = []
            for ws in list(self.user_connections[user_id]):
                try:
                    await ws.send_text(json.dumps(message))
                except Exception:
                    dead_sockets.append(ws)
            for ws in dead_sockets:
                self.user_connections[user_id].discard(ws)

    async def broadcast_to_role(self, role: str, message: dict):
        if role in self.role_connections:
            dead_sockets = []
            for ws in list(self.role_connections[role]):
                try:
                    await ws.send_text(json.dumps(message))
                except Exception:
                    dead_sockets.append(ws)
            for ws in dead_sockets:
                self.role_connections[role].discard(ws)

    async def broadcast_all(self, message: dict):
        dead_sockets = []
        for ws in list(self.active_connections):
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead_sockets.append(ws)
        for ws in dead_sockets:
            self.active_connections.discard(ws)

ws_manager = ConnectionManager()
