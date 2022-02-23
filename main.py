from __future__ import annotations
import asyncio
import json
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from lib.dataclass import MainEvents, PiWebSocket
from lib.database import PiState, connection_dict, state_dict

if os.environ.get("PYTHON_ENV") == "production":
    root_path = "/li-learn-timer/ws"
else:
    root_path = ""

app = FastAPI(root_path=root_path)

events = MainEvents()


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
            await connection.send(name, _props)
        else:
            await connection.send(name)


@app.websocket("/raspberry-pi")
async def ws_raspberry_pi(websocket: WebSocket):
    await websocket.accept()

    # クライアントを識別するためのIDを取得
    key = websocket.headers.get('sec-websocket-key')
    connection_dict[key] = PiWebSocket(ws=websocket)

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


async def on_message(key, data: dict):
    print(data)

    name: str = data.get("name", "")
    props: dict = data.get("props", {})

    if name != "ack":
        await connection_dict[key].send("ack")

    if name == "send_pi_id":
        if not(pi_id := props.get("pi_id")):
            return

        state = state_dict.get(pi_id)

        if state and state.is_running:
            # 実行中の場合
            state.connection_id = key

            # ToDo: send php reconnected
            return

        if state:
            # すでにタスクがセットしてある場合
            state.connection_id = key
        else:
            # タスクがまだセットされてない場合
            state = PiState(
                connection_id=key,
                tasks=[],
            )

            state_dict[pi_id] = state

        # ToDo: send php connected_pi

        if state.first_task:
            pass
            # ToDo: send pi ready_task
        else:
            pass
            # ToDo: send pi req_ready_task

    if name == "req_start_task":
        if not (state := state_dict.get_from_connection_id(key)):
            return
        elif state.first_task:
            pass
            # ToDo: send pi start_task
            # ToDo: send php started_task
        else:
            pass
            # ToDo: send pi cannot_start_task

    if name == "req_finish_task":
        if not (state := state_dict.get_from_connection_id(key)):
            return

        if 0 <= (length := state.length_to_finish):
            await asyncio.sleep(length)

        # ToDo: send pi finish_task
        # ToDo: send php finished_task

events.message.add_listener(on_message)
