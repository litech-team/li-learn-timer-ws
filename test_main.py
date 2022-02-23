from fastapi.testclient import TestClient

from lib.database import PiState, state_dict
from main import app

def test_ws_raspberry_pi_1():
    client = TestClient(app)

    with client.websocket_connect("/raspberry-pi") as websocket:
        websocket.send_json({
            "name": "send_pi_id",
            "props": {
                "pi_id": "01234"
            }
        })
        assert websocket.receive_json() == {
            "name": "ack"
        }