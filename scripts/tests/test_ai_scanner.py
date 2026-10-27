"""Regresiones del instalador y del comando de AI Scanner, sin claves ni escaneos reales."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("install_tmas", ROOT / "scripts/lib/install-tmas.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "security/ai-scanner").mkdir(parents=True)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("tmas", b"verified executable")
            archive.writestr("../../outside.txt", b"do not extract")
        self.archive = buffer.getvalue()
        self.pin = {"version": "2.335.0", "platforms": {"Darwin/arm64": {"filename": "tmas-cli_Darwin_arm64.zip", "sha256": hashlib.sha256(self.archive).hexdigest()}}}
        self.write_pin()
        first = patch.object(installer.platform, "system", return_value="Darwin")
        second = patch.object(installer.platform, "machine", return_value="arm64")
        first.start(); second.start()
        self.addCleanup(first.stop); self.addCleanup(second.stop)

    def write_pin(self):
        (self.root / "security/ai-scanner/tmas-cli.json").write_text(json.dumps(self.pin))

    def test_verified_install_extracts_only_binary_and_reuses_cache(self):
        with patch.object(installer.urllib.request, "urlopen", side_effect=lambda *args, **kwargs: io.BytesIO(self.archive)) as download:
            binary = installer.install(self.root)
            self.assertEqual(binary.read_bytes(), b"verified executable")
            self.assertEqual(binary.stat().st_mode & 0o777, 0o755)
            self.assertFalse((binary.parent.parent / "outside.txt").exists())
            self.assertEqual(installer.install(self.root), binary)
            self.assertEqual(download.call_count, 1)
            binary.write_bytes(b"tampered")
            installer.install(self.root)
            self.assertEqual(download.call_count, 2)
            self.assertEqual(binary.read_bytes(), b"verified executable")
            self.assertIn("/2.335.0/", download.call_args.args[0].full_url)
            self.assertNotIn("latest", download.call_args.args[0].full_url)

    def test_bad_checksum_is_rejected_before_extraction(self):
        self.pin["platforms"]["Darwin/arm64"]["sha256"] = "0" * 64
        self.write_pin()
        with patch.object(installer.urllib.request, "urlopen", return_value=io.BytesIO(self.archive)):
            with self.assertRaisesRegex(RuntimeError, "checksum"):
                installer.install(self.root)
        self.assertEqual(list(self.root.rglob("tmas")), [])

    def test_unsupported_platform_does_not_download(self):
        with patch.object(installer.platform, "system", return_value="Unknown"), patch.object(installer.urllib.request, "urlopen") as download:
            with self.assertRaisesRegex(RuntimeError, "Plataforma"):
                installer.install(self.root)
            download.assert_not_called()


class ScannerCommandTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "scripts/lib").mkdir(parents=True)
        (self.root / "security/ai-scanner").mkdir(parents=True)
        self.script = self.root / "scripts/run_ai_scanner.sh"
        shutil.copy2(ROOT / "scripts/run_ai_scanner.sh", self.script)
        self.log = self.root / "calls.jsonl"
        binary = self.root / "tmas-stub"
        binary.write_text("#!" + shutil.which("python3") + "\n" + f'''
import json, os, sys
from pathlib import Path
with open({str(self.log)!r}, 'a') as stream:
    stream.write(json.dumps({{'args': sys.argv[1:], 'target': os.getenv('TARGET_API_KEY'), 'tmas': os.getenv('TMAS_API_KEY'), 'cwd': os.getcwd()}}) + '\\n')
if 'validate' not in sys.argv:
    Path('ai-scanner-results.json').write_text('{{}}')
    Path('ai-scanner-report.md').write_text('# Test report')
''')
        binary.chmod(0o755)
        (self.root / "scripts/lib/install-tmas.py").write_text(f"print({str(binary)!r})\n")
        (self.root / "security/ai-scanner/tmas-aiscan-llm-config.yaml").write_text("version: 2.16.0\n")
        self.env = {key: value for key, value in os.environ.items() if key not in ("OPENAI_API_KEY", "TARGET_API_KEY", "TMAS_API_KEY", "AI_SCAN_RESULTS_DIR")}

    def run_script(self, *args):
        return subprocess.run(["bash", str(self.script), *args], env=self.env, cwd="/tmp", capture_output=True, text=True, timeout=15)

    def test_check_neither_loads_local_secrets_nor_starts_scan(self):
        marker = self.root / "loaded"
        (self.root / ".env.demo.local").write_text(f"touch {marker}\nexit 99\n")
        result = self.run_script("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(marker.exists())
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(len(calls), 1)
        self.assertIn("validate", calls[0]["args"])
        self.assertEqual(calls[0]["args"][:2], ["--env-file", "/dev/null"])
        self.assertIsNone(calls[0]["target"])

    def test_missing_openai_secret_fails_without_install_or_scan(self):
        self.env["TMAS_API_KEY"] = "test-tmas-secret"
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("OPENAI_API_KEY", result.stderr)
        self.assertNotIn("test-tmas-secret", result.stdout + result.stderr)
        self.assertFalse(self.log.exists())

    def test_explicit_credentials_override_local_file_and_outputs_are_separate(self):
        (self.root / ".env.demo.local").write_text('OPENAI_API_KEY="local-target"\nTMAS_API_KEY="local-tmas"\n')
        self.env.update(TARGET_API_KEY="explicit-target", TMAS_API_KEY="explicit-tmas")
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(len(calls), 2)
        scan = calls[1]
        self.assertEqual(scan["target"], "explicit-target")
        self.assertEqual(scan["tmas"], "explicit-tmas")
        self.assertIn("--yes", scan["args"])
        self.assertNotIn("--output", scan["args"])
        self.assertTrue(Path(scan["cwd"]).resolve().is_relative_to((self.root / ".runtime/ai-scanner/results").resolve()))
        self.assertTrue((Path(scan["cwd"]) / "ai-scanner-results.json").exists())
        self.assertNotIn("explicit-target", result.stdout + result.stderr)
