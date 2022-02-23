from __future__ import annotations

import asyncio
import json
import os
import traceback

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from lib.dataclass import PiState, MainEvents, PiWebSocket, ServerSocket
from lib.database import connection_dict, state_dict

if os.environ.get("PYTHON_ENV") == "production":
    root_path = "/li-learn-timer/ws"
else:
    root_path = ""

app = FastAPI(root_path=root_path)

events = MainEvents()

if (php_server_url := os.environ.get("PHP_SERVER_URL")):
    php_server = ServerSocket(php_server_url)
else:
    php_server = ServerSocket("http://localhost:8000/php_mock")


@app.get("/")
async def get():
    return HTMLResponse(r"<h1>Hello World</h1>")


@app.get("/send")
async def send_endpoint(name: str, props: str = ""):
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


class PHPEndpointBody(BaseModel):
    name: str
    props: dict = {}


@app.post("/local/php")
async def php_endpoint(body: PHPEndpointBody):
    name = body.name
    props = body.props

    if name != "ack":
        await php_server.send("ack")


@app.post("/php_mock")
async def php_mock_endpoint(body: PHPEndpointBody):
    print(body)


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


async def on_message(key, name: str, props: dict):
    if name != "ack":
        await connection_dict[key].send("ack")

    if name == "send_pi_id":
        if not(pi_id := props.get("pi_id")):
            return

        state = state_dict.get(pi_id)

        if state and state.is_running:
            # 実行中の場合
            state.connection_id = key

            await php_server.send("reconnected_pi", {"pi_id": pi_id})
            return

        if state:
            print("al")
            # すでにタスクがセットしてある場合
            state.connection_id = key
        else:
            # タスクがまだセットされてない場合
            state = PiState(
                connection_id=key,
                tasks=[],
            )

            state_dict[pi_id] = state

        if (first_task := state.first_task):
            await connection_dict[key].send("ready_task", {"task": first_task})
        else:
            await connection_dict[key].send("req_ready_task")

        await php_server.send("connected_pi", {"pi_id": pi_id})

    if name == "req_start_task":
        if not (state := state_dict.get_from_connection_id(key)):
            return
        elif (first_task := state.first_task):
            state.start_task(first_task)
            props = {"task": first_task, "length": len(state.tasks)}
            await connection_dict[key].send("start_task", props)
            await php_server.send("started_task", props)
        else:
            await php_server.send("cannot_start_task")

    if name == "req_finish_task":
        if not (state := state_dict.get_from_connection_id(key)):
            return

        if 0 <= (length := state.length_to_finish):
            await asyncio.sleep(length)

        state.finish_task()

        if (next_task := state.first_task):
            props = {"next_task": next_task, "tasks_length": len(state.tasks)}
        else:
            props = {"next_task": None, "tasks_length": 0}

        await connection_dict[key].send("finish_task", props)
        await php_server.send("finished_task", props)


async def on_message_wapper(key, data: dict):
    try:
        name: str = data["name"]
        props: dict = data.get("props", {})
        await on_message(key, name, props)
    except:
        print(traceback.format_exc())


events.message.add_listener(on_message_wapper)
