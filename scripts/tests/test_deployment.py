"""Pruebas del despliegue con herramientas simuladas; no contactan con el clúster."""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="trendo-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "scripts", self.root / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(ROOT / "k8s", self.root / "k8s", ignore=shutil.ignore_patterns("*secret*"))
        self.values = {
            "OPENAI_API_KEY": 'test-quote"-slash\\-dollar$-single\'',
            "TREND_API_KEY": "test-trend",
            "FILE_SECURITY_API_KEY": "test-file",
            "FILE_SECURITY_REGISTRATION_TOKEN": "test-registration",
            "FILE_SECURITY_HOST": "custom-scanner.example:50051",
            "TREND_AI_URL": "https://guard.example",
            "TREND_AI_APP_NAME": "test-demo",
            "BACKEND_LOCAL_PORT": "19000",
            "FRONTEND_LOCAL_PORT": "18081",
        }
        self.write_env()
        for name, entries in (("backend", ["Dockerfile", ".dockerignore", "requirements.lock", "main.py", "app"]), ("frontend", ["Dockerfile", ".dockerignore", "nginx.conf", "package.json", "package-lock.json", "index.html", "vite.config.js", "src", "public"])):
            for entry in entries:
                source = ROOT / f"portal-{name}" / entry
                target = self.root / f"portal-{name}" / entry
                target.parent.mkdir(parents=True, exist_ok=True)
                if source.is_dir():
                    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__"))
                else:
                    shutil.copy2(source, target)
        self.log = self.root / "commands.jsonl"
        binary = self.root / "bin"
        binary.mkdir()
        stub = binary / "stub"
        stub.write_text("#!" + shutil.which("python3") + "\n" + '''
import json, os, sys, time, signal
from pathlib import Path
name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ["TEST_COMMAND_LOG"], "a") as stream:
    stream.write(json.dumps([name] + args) + "\\n")
if name == "kubectl" and "get" in args and "device-token-secret" in args:
    if os.getenv("TEST_SECRET_QUERY_FAIL"):
        sys.exit(1)
    if os.getenv("TEST_DEVICE_EXISTS"):
        print("secret/device-token-secret")
if name == "kubectl" and "port-forward" in args:
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    while True:
        time.sleep(0.05)
''')
        stub.chmod(0o755)
        for name in ("kubectl", "helm", "colima", "docker", "curl", "pkill", "sleep", "nohup"):
            (binary / name).symlink_to(stub)
        self.env = {**os.environ, "PATH": str(binary) + ":" + os.environ["PATH"],
                    "TEST_COMMAND_LOG": str(self.log)}
        self.addCleanup(lambda: self.run_script("parar_ports.sh"))

    def write_env(self):
        (self.root / ".env.demo.local").write_text("\n".join(
            key + "=" + shlex.quote(value) for key, value in self.values.items()
        ))

    def run_script(self, name="desplegar_demo_full_v2.sh", *args):
        return subprocess.run(["zsh", "-f", str(self.root / "scripts" / name), *args],
                              cwd="/tmp", env=self.env, capture_output=True, text=True, timeout=30)

    def commands(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_check_does_not_call_runtime_or_create_state(self):
        result = self.run_script("desplegar_demo_full_v2.sh", "--check")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertFalse(self.log.exists())
        self.assertFalse((self.root / ".runtime").exists())

    def test_placeholder_is_rejected_before_runtime(self):
        self.values["OPENAI_API_KEY"] = "RELLENAR"
        self.write_env()
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.log.exists())

    def test_invalid_ports_are_rejected(self):
        for value in ("abc", "0", "65536", "18081"):
            self.values["BACKEND_LOCAL_PORT"] = value
            self.write_env()
            result = self.run_script("desplegar_demo_full_v2.sh", "--check")
            self.assertNotEqual(result.returncode, 0, value)
        self.assertFalse(self.log.exists())

    def test_full_flow_uses_context_safe_secrets_and_http_checks(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        commands = self.commands()
        for command in commands:
            if command[0] in ("kubectl", "helm"):
                flag = "--context" if command[0] == "kubectl" else "--kube-context"
                self.assertEqual(command[1:3], [flag, "colima"])
        forwards = [c for c in commands if c[0] == "kubectl" and "port-forward" in c]
        self.assertEqual(len(forwards), 2)
        self.assertTrue(all(c[1:3] == ["--context", "colima"] for c in forwards))
        secret_file = self.root / ".runtime/secrets/application.json"
        application = json.loads(secret_file.read_text())["items"]
        self.assertEqual(application[0]["stringData"]["OPENAI_API_KEY"], self.values["OPENAI_API_KEY"])
        self.assertEqual(application[2]["stringData"]["FILE_SECURITY_HOST"], self.values["FILE_SECURITY_HOST"])
        self.assertEqual(application[1]["stringData"]["TREND_AI_URL"], self.values["TREND_AI_URL"])
        self.assertEqual(application[1]["stringData"]["TREND_AI_APP_NAME"], self.values["TREND_AI_APP_NAME"])
        self.assertEqual(secret_file.stat().st_mode & 0o777, 0o600)
        items = json.loads((self.root / ".runtime/secrets/file-security.json").read_text())["items"]
        self.assertEqual([item["metadata"]["name"] for item in items], ["token-secret", "device-token-secret"])
        self.assertFalse((self.root / "k8s/secret.yaml").exists())
        self.assertTrue(any(c[0] == "curl" and "http://127.0.0.1:18081/" in c for c in commands))
        self.assertFalse(any(c[0] == "curl" and any("/api/chat" in a for a in c) for c in commands))

    def test_existing_device_registration_is_preserved(self):
        self.env["TEST_DEVICE_EXISTS"] = "1"
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        items = json.loads((self.root / ".runtime/secrets/file-security.json").read_text())["items"]
        self.assertEqual([item["metadata"]["name"] for item in items], ["token-secret"])

    def test_secret_query_failure_aborts_without_applying_secrets(self):
        self.env["TEST_SECRET_QUERY_FAIL"] = "1"
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / ".runtime/secrets/application.json").exists())
        self.assertFalse(any("upgrade" in c for c in self.commands()))

    def test_stop_uses_same_context(self):
        result = self.run_script("apagar_demo_full.sh")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        for command in self.commands():
            if command[0] == "kubectl":
                self.assertEqual(command[1:3], ["--context", "colima"])
            if command[0] == "helm":
                self.assertEqual(command[1:3], ["--kube-context", "colima"])


if __name__ == "__main__":
    unittest.main()
