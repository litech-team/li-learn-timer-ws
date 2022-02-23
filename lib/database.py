from __future__ import annotations
from typing import Dict

from lib.dataclass import PiState, PiWebSocket


class StateDict(Dict[str, PiState]):
    def get_from_connection_id(self, connection_id):
        if not (connection := connection_dict.get(connection_id)):
            return None
        elif not (pi_id := connection.pi_id):
            return None
        elif not (state := self.get(pi_id)):
            return None
        else:
            return state


connection_dict: dict[str, PiWebSocket] = {}
state_dict: StateDict = StateDict()
