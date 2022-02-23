import pytest
from pytest_mock import MockerFixture

from lib.dataclass import MockServerSocket
from lib.database import state_dict, connection_dict

from fastapi.testclient import TestClient
from main import app

php_server = MockServerSocket()


@pytest.fixture(scope='function', autouse=True)
def scope_function(mocker: MockerFixture):
    php_server.mock(mocker, "lib.dataclass.ServerSocket")
    yield
    php_server.clear()
    for key in list(connection_dict):
        del connection_dict[key]
    for key in list(state_dict):
        del state_dict[key]


def test_php_endpoint():
    client = TestClient(app)

    client.post("/local/php", json={
        "name": "send_tasks",
        "props": {
            "tasks": []
        }
    })

    assert php_server.receive_json() == {
        "name": "ack"
    }


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
