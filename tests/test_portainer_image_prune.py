import importlib.util
import io
import json
import types
import unittest
from contextlib import redirect_stdout
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "skills/portainer/scripts/portainer.py"
SPEC = importlib.util.spec_from_file_location("portainer", SCRIPT_PATH)
portainer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(portainer)


class FakeClient:
    def __init__(self, result):
        self.result = result
        self.path = None

    def post(self, path):
        self.path = path
        return self.result


def request_filters(client):
    query = client.path.split("?", 1)[1]
    encoded_filters = query.split("filters=", 1)[1]
    return json.loads(portainer.urllib.parse.unquote(encoded_filters))


class ImagePruneTests(unittest.TestCase):
    def run_prune(self, all_images=False, result=None):
        client = FakeClient(result or {"SpaceReclaimed": 0, "ImagesDeleted": []})
        args = types.SimpleNamespace(endpoint=5, all=all_images)
        with redirect_stdout(io.StringIO()):
            portainer.cmd_image_prune(client, args)
        return client

    def test_default_prune_uses_docker_filter_array(self):
        client = self.run_prune()

        self.assertEqual(request_filters(client), {"dangling": ["true"]})

    def test_cli_default_prune_only_targets_dangling_images(self):
        client = FakeClient({"SpaceReclaimed": 0, "ImagesDeleted": []})
        args = portainer.build_parser().parse_args(["image-prune", "5"])
        with redirect_stdout(io.StringIO()):
            portainer.cmd_image_prune(client, args)

        self.assertEqual(request_filters(client), {"dangling": ["true"]})

    def test_all_prune_uses_docker_filter_array(self):
        client = self.run_prune(all_images=True)

        self.assertEqual(request_filters(client), {"dangling": ["false"]})

    def test_cli_all_prune_accepts_true_string(self):
        client = FakeClient({"SpaceReclaimed": 0, "ImagesDeleted": []})
        args = portainer.build_parser().parse_args(["image-prune", "5", "true"])
        with redirect_stdout(io.StringIO()):
            portainer.cmd_image_prune(client, args)

        self.assertEqual(request_filters(client), {"dangling": ["false"]})

    def test_null_images_deleted_is_treated_as_empty(self):
        self.run_prune(result={"SpaceReclaimed": 0, "ImagesDeleted": None})


if __name__ == "__main__":
    unittest.main()
