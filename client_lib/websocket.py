from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json

from websockets import client as websockets


class EventHandler:
    def __init__(self):
        self.listeners = []

    def add_listener(self, listener):
        self.listeners.append(listener)
        return self

    def remove_listener(self, listener):
        self.listeners.remove(listener)
        return self

    def fire(self, *args):
        for listener in self.listeners:
            if (asyncio.iscoroutinefunction(listener)):
                asyncio.ensure_future(listener(*args))
            else:
                listener(*args)


@dataclass
class WebSocketEvents:
    message = EventHandler()
    connect = EventHandler()
    close = EventHandler()


class WebSocket:
    def __init__(self, url) -> None:
        self.url = url
        self.events = WebSocketEvents()
        self.ws = None
        self.close_flag = False

        asyncio.ensure_future(self.eventloop())

    async def send(self, data):
        if self.ws:
            message = json.dumps(data)
            await self.ws.send(message)

    async def close(self):
        self.close_flag = True

        if self.ws:
            await self.ws.close()

    async def eventloop(self):
        while True:
            if self.close_flag:
                break

            while not self.ws:
                try:
                    self.ws = await websockets.connect(self.url)
                    self.events.connect.fire()
                except:
                    await asyncio.sleep(0.5)

            while self.ws:
                try:
                    message = await self.ws.recv()
                    data = json.loads(message)
                    self.events.message.fire(data)
                except:
                    self.events.close.fire()
                    self.ws = None

    def listen_events(self, *, on_message, on_connect, on_close):
        if on_message:
            self.events.message.add_listener(on_message)
        if on_connect:
            self.events.connect.add_listener(on_connect)
        if on_close:
            self.events.close.add_listener(on_close)

    def wait_end(self):
        loop = asyncio.get_event_loop()
        pending_tasks = asyncio.all_tasks(loop)
        loop.run_until_complete(asyncio.gather(*pending_tasks))


def set_timeout(callback, delay: float, *args):
    async def fnc():
        await asyncio.sleep(delay)
        if (asyncio.iscoroutinefunction(callback)):
            await callback(*args)
        else:
            callback(*args)

    asyncio.ensure_future(fnc())


sleep = asyncio.sleep
run_async = asyncio.run
