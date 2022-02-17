from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from lib.websocket import WebSocketHandler

handler_dict: dict[str, WebSocketHandler] = {}

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
    handler_dict[key] = WebSocketHandler(websocket)

    async def fnc(handler, data):
        print(data)
        await handler.send_json({"value": f"res-{data['value']}"})
        print("send end")

    handler_dict[key].add_listener(fnc)

    try:
        while True:
            data = await websocket.receive_json()
            handler_dict[key].fire(data)
    except WebSocketDisconnect:
        if handler_dict[key]:
            del handler_dict[key]
            await websocket.close()