import json
from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections per restaurant."""

    def __init__(self):
        # restaurant_id -> list of connected websockets
        self.active: Dict[str, List[WebSocket]] = {}

    async def connect(self, restaurant_id: str, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(restaurant_id, []).append(ws)

    def disconnect(self, restaurant_id: str, ws: WebSocket):
        if restaurant_id in self.active:
            self.active[restaurant_id].discard(ws) if hasattr(self.active[restaurant_id], 'discard') else None
            try:
                self.active[restaurant_id].remove(ws)
            except ValueError:
                pass

    async def broadcast(self, restaurant_id: str, data: dict):
        """Send JSON payload to all connections for a restaurant."""
        if restaurant_id not in self.active:
            return
        dead = []
        for ws in self.active[restaurant_id]:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(restaurant_id, ws)


manager = ConnectionManager()
