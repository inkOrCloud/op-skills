import importlib.util
from argparse import Namespace
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "skills/portainer/scripts/portainer.py"
SPEC = importlib.util.spec_from_file_location("portainer", SCRIPT_PATH)
portainer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(portainer)


class RecordingClient:
    def __init__(self):
        self.calls = []

    def post(self, path, payload):
        self.calls.append((path, payload))
        return {"Id": "a" * 64}


def test_container_create_uses_host_network_mode_for_host_network(capsys):
    client = RecordingClient()
    args = Namespace(
        name="sse-probe-robish",
        image="python:3.12-alpine",
        cmd="python -m http.server",
        volume=[],
        env=[],
        entrypoint="",
        network="host",
        restart="no",
        no_start=True,
        endpoint=10,
    )

    portainer.cmd_container_create(client, args)

    create_path, config = client.calls[0]
    assert create_path == "/endpoints/10/docker/containers/create?name=sse-probe-robish"
    assert config["HostConfig"]["NetworkMode"] == "host"
    assert "NetworkingConfig" not in config
    assert len(client.calls) == 1
    assert "created" in capsys.readouterr().out


def test_container_create_attaches_non_host_network(capsys):
    client = RecordingClient()
    args = Namespace(
        name="app",
        image="app:latest",
        cmd="",
        volume=[],
        env=[],
        entrypoint="",
        network="mynet",
        restart="no",
        no_start=True,
        endpoint=4,
    )

    portainer.cmd_container_create(client, args)

    _, config = client.calls[0]
    assert "NetworkMode" not in config["HostConfig"]
    assert config["NetworkingConfig"] == {"EndpointsConfig": {"mynet": {}}}
    assert "created" in capsys.readouterr().out
