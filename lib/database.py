from __future__ import annotations
from typing import Dict

from lib.dataclass import PiState

from fastapi import WebSocket


class StateDict(Dict[str, PiState]):
    def get_from_connection_id(self, connection_id):
        if not (pi_id := connection_pi_id_dict.get(connection_id)):
            return None
        elif not (state := self.get(pi_id)):
            return None
        else:
            return state


connection_dict: dict[str, WebSocket] = {}
connection_pi_id_dict: dict[str, str] = {}
state_dict: StateDict = StateDict()
