from __future__ import annotations
from dataclasses import dataclass
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from lib.event import EventHandler

connection_dict: dict[str, WebSocket] = {}


@dataclass
class Events:
    message = EventHandler()
    connect = EventHandler()
    close = EventHandler()


events = Events()

app = FastAPI()


@app.get("/")
async def get():
    return HTMLResponse(r"<h1>Hello World</h1>")


@app.get("/send")
async def send_endpoind(name: str, props: str = ""):
    if props:
        try:
            _props = json.loads(props)
        except:
            _props = None
    else:
        _props = None

    for (key, connection) in connection_dict.items():
        if _props:
            await connection.send_json({"name": name, "props": _props})
        else:
            await connection.send_json({"name": name})


@app.websocket("/raspberry-pi")
async def ws_raspberry_pi(websocket: WebSocket):
    await websocket.accept()

    # クライアントを識別するためのIDを取得
    key = websocket.headers.get('sec-websocket-key')
    connection_dict[key] = websocket

    events.connect.fire(key, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            events.message.fire(key, data)
    except WebSocketDisconnect:
        if connection_dict[key]:
            del connection_dict[key]

        await websocket.close()
        events.close.fire(key)


async def on_message(key, data):
    print(data)

    if data["name"] != "ack":
        await connection_dict[key].send_json({"name": "ack"})

events.message.add_listener(on_message)
