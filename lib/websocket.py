from fastapi import WebSocket
from lib.event import EventHandler

class WebSocketHandler(EventHandler):
    def __init__(self, websocket: WebSocket):
        super().__init__()
        self.websocket = websocket
    
    async def send_json(self, value):
        await self.websocket.send_json(value)
