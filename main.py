from __future__ import annotations
from typing import cast, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from lib.event import EventHandler

connection_dict: Dict[str, WebSocket] = {}

ws_event = {
    "connect": EventHandler(),
    "message": cast(Dict[str, EventHandler], {}),
    "disconnect": EventHandler(),
}

app = FastAPI()

html = r"""
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var { value } = JSON.parse(event.data)
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(value)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(JSON.stringify({value: input.value}))
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # クライアントを識別するためのIDを取得
    key = websocket.headers.get('sec-websocket-key')
    connection_dict[key] = websocket
    ws_event["message"][key] = EventHandler()

    ws_event["connect"].fire(key, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            ws_event["message"][key].fire(data)
    except WebSocketDisconnect:
        if ws_event["message"][key]:
            del ws_event["message"][key]
        if connection_dict[key]:
            del connection_dict[key]

        await websocket.close()
        ws_event["disconnect"].fire(key)


def on_connect_websocket(handler, key: str, websocket: WebSocket):
    async def listener(handler, data):
        print(data)
        await connection_dict[key].send_json({"value": f"res-{data['value']}"})
        print("send end")

    ws_event["message"][key].add_listener(listener)


ws_event["connect"].add_listener(on_connect_websocket)
