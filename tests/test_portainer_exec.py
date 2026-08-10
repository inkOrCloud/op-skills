import importlib.util
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "skills/portainer/scripts/portainer.py"
SPEC = importlib.util.spec_from_file_location("portainer_exec", SCRIPT_PATH)
portainer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(portainer)


class FakeExecClient:
    def __init__(self):
        self.calls = []

    def exec_run(self, endpoint, container, cmd, tty=False):
        self.calls.append((endpoint, container, tuple(cmd), tty))
        return b"", b""


class ExecEndpointTests(unittest.TestCase):
    def run_exec(self, argv):
        client = FakeExecClient()
        args = portainer.build_parser().parse_args(argv)
        with redirect_stdout(io.StringIO()):
            portainer.cmd_exec(client, args)
        return client

    def test_endpoint_after_container(self):
        client = self.run_exec(
            ["exec", "caddy", "--endpoint", "10", "cat", "/etc/caddy/Caddyfile"]
        )

        self.assertEqual(
            client.calls,
            [(10, "caddy", ("cat", "/etc/caddy/Caddyfile"), False)],
        )

    def test_short_endpoint_after_container(self):
        client = self.run_exec(["exec", "caddy", "-e", "10", "cat", "/data"])

        self.assertEqual(client.calls, [(10, "caddy", ("cat", "/data"), False)])

    def test_endpoint_before_container(self):
        client = self.run_exec(
            ["exec", "--endpoint", "10", "caddy", "cat", "/data"]
        )

        self.assertEqual(client.calls, [(10, "caddy", ("cat", "/data"), False)])

    def test_default_endpoint(self):
        client = self.run_exec(["exec", "caddy", "cat", "/data"])

        self.assertEqual(client.calls, [(4, "caddy", ("cat", "/data"), False)])

    def test_endpoint_equals_after_container(self):
        client = self.run_exec(["exec", "caddy", "--endpoint=10", "cat", "/data"])

        self.assertEqual(client.calls, [(10, "caddy", ("cat", "/data"), False)])

    def test_command_arguments_after_command_are_preserved(self):
        client = self.run_exec(["exec", "caddy", "cat", "--endpoint", "10", "/data"])

        self.assertEqual(
            client.calls,
            [(4, "caddy", ("cat", "--endpoint", "10", "/data"), False)],
        )

    def test_invalid_endpoint_after_container_exits(self):
        args = portainer.build_parser().parse_args(
            ["exec", "caddy", "--endpoint", "abc", "cat", "/data"]
        )

        with self.assertRaises(SystemExit):
            portainer.cmd_exec(FakeExecClient(), args)


if __name__ == "__main__":
    unittest.main()
