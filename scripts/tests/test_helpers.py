import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts/lib" / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


images = module("build_images", "build-images.py")
ports = module("port_forwards", "port-forwards.py")


class HelperTests(unittest.TestCase):
    def test_image_tag_changes_with_source_but_not_python_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app").mkdir()
            source = root / "app/main.py"
            source.write_text("one")
            first = images.source_digest(root, ["app"])
            (root / "app/__pycache__").mkdir()
            (root / "app/__pycache__/main.pyc").write_bytes(b"cache")
            self.assertEqual(first, images.source_digest(root, ["app"]))
            source.write_text("two")
            self.assertNotEqual(first, images.source_digest(root, ["app"]))

    def test_env_update_handles_quotes_and_preserves_other_values(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / ".env"
            target.write_text("KEEP=unchanged\nTOKEN=old\n")
            value = "quote'\"-dollar$-slash\\"
            subprocess.run(["python3", str(ROOT / "scripts/lib/update-env.py"), str(target), "TOKEN"], input=value, text=True, check=True)
            result = subprocess.run(["bash", "-c", 'source "$1"; printf "%s" "$TOKEN"', "bash", str(target)], capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout, value)
            self.assertIn("KEEP=unchanged", target.read_text())
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_stop_does_not_kill_reused_or_unrelated_pid(self):
        record = {"pid": 123, "argv": ["kubectl", "--context", "colima", "port-forward", "-n", "trendo-demo", "service/backend-service", "9000:8007"]}
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "process.json"
            state.write_text(json.dumps([record]))
            with patch.object(ports, "process_command", return_value="unrelated-process"), patch.object(ports.os, "kill") as kill:
                ports.stop_owned(state)
                kill.assert_not_called()
            self.assertFalse(state.exists())

    def test_stop_checks_entire_context_service_and_port(self):
        argv = ["kubectl", "--context", "colima", "port-forward", "-n", "trendo-demo", "service/backend-service", "9000:8007"]
        with patch.object(ports, "process_command", return_value=" ".join(argv)):
            self.assertTrue(ports.matches({"pid": 123, "argv": argv}))
        for changed in (" ".join(argv).replace("colima", "production"), " ".join(argv).replace("9000", "9001")):
            with patch.object(ports, "process_command", return_value=changed):
                self.assertFalse(ports.matches({"pid": 123, "argv": argv}))
