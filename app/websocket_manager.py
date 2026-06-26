import logging
from typing import Dict, List
from fastapi import WebSocket


logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages all active Websocket connections.
    Tracks which users are connected and which sockets they have open
    One user can have multiple connections (multiple browser tabs)
    """

    def __init__(self):
        # user_id -> list o websocket connections
        # dict - one user can connect from multiple devices/tabs\
        self.active_connections: Dict[int, List[WebSocket]] = {}

    
    async def connect(self, websocket: WebSocket, user_id: int):
        """
        Accept a new websocket connection and register it
        """
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)
        logger.info(
            f"[WS] user_id={user_id} connected. "
            f"Total connections for user: {len(self.active_connections[user_id])}"
        )

    def disconnect(self, websocket: WebSocket, user_id: int):
        "Remove a websocket when client disconnects."
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)

            # clean up empty lists
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        logger.info(
            f"[WS] user_id={user_id} disconnected. "
            f"Active users: {len(self.active_connections)}"
        )
    
    async def send_to_user(self, user_id: int, message: dict):
        """
        Send a json message to all connections for a specific user.
        if user has 3 browser tabs open, all 3 recieve the message.
        """
        if user_id not in self.active_connections:
            logger.info(f"[WS] user_id={user_id} not connected - skipping push")
            return

        disconnected = []

        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_json(message)
                logger.info(f"[WS] pushed to user_id={user_id}: {message['type']}")
            except Exception as e:
                logger.warning(f"[WS] failed to send to user_id={user_id}: {e}")
                disconnected.append(websocket)

        
        # clean up any dead connections
        for ws in disconnected:
            self.active_connections[user_id].remove(ws)

    async def broadcast(self, message: dict):
        """
        Send a message to all connected users
        user for system-wide announcements
        """
        for user_id, connections in self.active_connections.items():
            for websocket in connections:
                try:
                    await websocket.send_json(message)
                except Exception:
                    pass

    
    @property
    def connected_user_count(self) -> int:
        # number of unique users currently connected
        return len(self.active_connections)
    

    @property
    def total_connection_count(self) -> int:
        # total WS connections count(multiple per user possible)
        return sum(len(conns) for conns in self.active_connections.values())
    

# single instance shared across entire app
# in prod with multiple servers you user redis pub/sub
manager = ConnectionManager()