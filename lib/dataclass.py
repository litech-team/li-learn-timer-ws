from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from lib.event import EventHandler

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