from __future__ import annotations
import asyncio
from datetime import datetime
from dataclasses import dataclass
import json
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from lib.event import EventHandler


if os.environ.get("PYTHON_ENV") == "production":
    root_path = "/li-learn-timer/ws"
else:
    root_path = ""

app = FastAPI(root_path=root_path)

connection_dict: dict[str, WebSocket] = {}

connection_pi_id_dict: dict[str, str] = {}


@dataclass
class Task:
    name: str
    started: datetime | None


@dataclass
class PiState:
    connection_id: str | None
    tasks: list[Task]

    @property
    def is_running(self) -> bool:
        return not all(task.started == None for task in self.tasks)

    @property
    def first_task(self) -> Task | None:
        if len(self.tasks):
            return self.tasks[0]
        else:
            return None

    @property
    def length_to_finish(self) -> float:
        now = datetime.now()
        l: list[float] = []

        for task in self.tasks:
            if task.started:
                l.append((now - task.started).total_seconds())

        return max(*l)


state_dict: dict[str, PiState] = {}


@dataclass
class Events:
    message = EventHandler()
    connect = EventHandler()
    close = EventHandler()


events = Events()


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


def get_state(connection_id: str) -> PiState | None:
    if not (pi_id := connection_pi_id_dict.get(connection_id)):
        return None
    elif not (state := state_dict.get(pi_id)):
        return None
    else:
        return state


async def on_message(key, data: dict):
    print(data)

    name: str = data.get("name", "")
    props: dict = data.get("props", {})

    if name != "ack":
        await connection_dict[key].send_json({"name": "ack"})

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
        if not (state := get_state(key)):
            return
        elif state.first_task:
            pass
            # ToDo: send pi start_task
            # ToDo: send php started_task
        else:
            pass
            # ToDo: send pi cannot_start_task

    if name == "req_finish_task":
        if not (state := get_state(key)):
            return

        if 0 <= (length := state.length_to_finish):
            await asyncio.sleep(length)

        # ToDo: send pi finish_task
        # ToDo: send php finished_task

events.message.add_listener(on_message)
