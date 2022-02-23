from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from pytest_mock.plugin import MockerFixture
import aiohttp

from lib.event import EventHandler

from fastapi import WebSocket


@dataclass
class ServerSocket:
    url: str

    async def send(self, name: str, props: dict = None):
        async with aiohttp.ClientSession() as session:
            if props:
                await session.post(self.url, json={"name": name, "props": props})
            else:
                await session.post(self.url, json={"name": name})

@dataclass
class MockServerSocket:
    stack: list = field(default_factory=list)

    async def send(self, name: str, props: dict = None):
        if props:
            self.stack.append({"name": name, "props": props})
        else:
            self.stack.append({"name": name})

    def receive_json(self):
        return self.stack.pop(0)
    
    def mock(self, mocker: MockerFixture, target: str):
        mocker.patch(f'{target}.send', side_effect=self.send)
    
    def clear(self):
        self.stack = []



@dataclass
class PiWebSocket:
    ws: WebSocket
    pi_id: str | None = None

    async def send(self, name: str, props: dict = None):
        if props:
            await self.ws.send_json({"name": name, "props": props})
        else:
            await self.ws.send_json({"name": name})


@dataclass
class MainEvents:
    message = EventHandler()
    connect = EventHandler()
    close = EventHandler()


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
