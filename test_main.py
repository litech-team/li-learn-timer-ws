import pytest

from lib.database import state_dict, connection_dict

from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope='function', autouse=True)
def scope_function():
    yield
    for key in list(connection_dict):
        del connection_dict[key]
    for key in list(state_dict):
        del state_dict[key]

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
        assert websocket.receive_json() == {
            "name": "req_ready_task"
        }