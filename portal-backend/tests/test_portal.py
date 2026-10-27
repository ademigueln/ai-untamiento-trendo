import io
import json
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
import tempfile
from datetime import datetime, timezone
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from fastapi import UploadFile
from fastapi.testclient import TestClient
from main import app
from app.core.config import settings
from app.services import ai_events, ai_guard, file_security, memory, storage, stats

ALLOW = {"allowed": True, "reason": None, "source": "trend_ai_guard"}
BLOCK = {"allowed": False, "reason": "prompt injection", "source": "trend_ai_guard", "event_type": "prompt_injection_blocked"}
CLEAN = {"result": {"atse": {"malwareCount": 0, "error": ""}}}


class PortalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        configured = replace(settings, upload_dir=self.root / "uploads", events_db=self.root / "events.sqlite3", max_upload_bytes=128, openai_api_key="test", trend_api_key="test", file_security_api_key="test", guard_fail_open=False)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for module in ("app.core.config", "app.core.upload_limit", "app.services.ai_events", "app.services.ai_guard", "app.services.chatbot", "app.services.memory", "app.services.storage", "app.services.file_security", "app.services.stats"):
            self.stack.enter_context(patch(module + ".settings", configured))
        with memory._lock:
            memory._sessions.clear()
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def chat(self, message="consulta", token=None):
        body = {"message": message}
        if token:
            body["conversation_id"] = token
        return self.client.post("/api/chat", json=body)

    def test_sessions_isolate_history_and_delete_really_clears(self):
        with patch("app.routes.chat.inspect_prompt", return_value=ALLOW), patch("app.routes.chat.inspect_output", return_value=ALLOW), patch("app.routes.chat.get_ai_reply", return_value="respuesta") as llm:
            first = self.chat("uno").json()["conversation_id"]
            self.chat("dos")
            self.assertEqual(llm.call_args.args[1], [])
            self.chat("tres", first)
            self.assertEqual(llm.call_args.args[1], [{"role": "user", "content": "uno"}, {"role": "assistant", "content": "respuesta"}])
            self.assertEqual(self.client.delete(f"/api/chat/{first}").status_code, 204)
            self.assertEqual(self.chat(token=first).status_code, 404)

    def test_blocked_output_is_not_saved_or_returned(self):
        with patch("app.routes.chat.inspect_prompt", return_value=ALLOW), patch("app.routes.chat.inspect_output", return_value=BLOCK), patch("app.routes.chat.get_ai_reply", return_value="PRIVATE_OUTPUT"):
            response = self.chat()
        self.assertNotIn("PRIVATE_OUTPUT", response.text)
        token = response.json()["conversation_id"]
        self.assertEqual(list(memory._sessions[token].messages), [])
        self.assertEqual(ai_events.count_ai_events()["trend_guard_blocked"], 1)

    def test_input_block_does_not_call_llm(self):
        with patch("app.routes.chat.inspect_prompt", return_value=BLOCK), patch("app.routes.chat.get_ai_reply") as llm:
            self.assertEqual(self.chat().json()["guard_action"], "blocked_input")
            llm.assert_not_called()

    def test_guard_unknown_response_fails_closed_and_is_visible(self):
        with patch("app.services.ai_guard.call_trend_ai_guard", return_value={"status": "ok", "result": {}}), patch("app.routes.chat.get_ai_reply") as llm:
            self.assertEqual(self.chat().status_code, 503)
            llm.assert_not_called()
        panel = self.client.get("/api/stats").json()
        self.assertEqual(panel["portal_status"], "Degradado")
        self.assertEqual(panel["services"]["ai_guard"], "unavailable")

    def test_explicit_permissive_mode_is_degraded_and_not_saved(self):
        permissive = replace(ai_guard.settings, guard_fail_open=True)
        with patch.object(ai_guard, "settings", permissive), patch("app.services.ai_guard.call_trend_ai_guard", return_value={"status": "error"}), patch("app.routes.chat.get_ai_reply", return_value="respuesta"):
            result = self.chat().json()
        self.assertEqual(result["guard_action"], "degraded")
        self.assertEqual(list(memory._sessions[result["conversation_id"]].messages), [])

    def test_history_ttl_capacity_and_concurrent_session_guard(self):
        with memory.conversation(None) as (token, _):
            for _ in range(10):
                memory.add_exchange(token, "u", "a")
            self.assertEqual(len(memory._sessions[token].messages), 6)
            with self.assertRaises(Exception) as failure:
                memory.clear_memory(token)
            self.assertEqual(failure.exception.status_code, 409)
            with self.assertRaises(Exception):
                with memory.conversation(token):
                    pass
        memory._sessions[token].touched -= settings.session_ttl + 1
        with self.assertRaises(Exception) as failure:
            with memory.conversation(token):
                pass
        self.assertEqual(failure.exception.status_code, 404)
        with patch.object(memory, "settings", replace(memory.settings, session_limit=1)):
            with memory.conversation(None):
                pass
            with self.assertRaises(Exception) as failure:
                with memory.conversation(None):
                    pass
            self.assertEqual(failure.exception.status_code, 503)

    def test_unknown_scan_contract_never_clean(self):
        for result in ({}, [], None, {"status": "raw_result"}, {"result": {"atse": {}}}, {"result": {"atse": {"malwareCount": False}}}, {"result": {"atse": {"malwareCount": "0"}}}, {"result": {"atse": {"malwareCount": 0, "malware": ["detection"]}}}):
            self.assertEqual(storage.classify_result(result), "error")
        self.assertEqual(storage.classify_result(CLEAN), "clean")
        self.assertEqual(storage.classify_result({"result": {"atse": {"malwareCount": 1}}}), "malicious")

    def test_uploads_are_confined_unique_and_unknown_scans_stay_incoming(self):
        with patch("app.services.storage.scan_file", return_value=CLEAN):
            results = [self.client.post("/api/files/upload", files={"file": ("../../same.txt", b"abc")}).json() for _ in range(2)]
        self.assertNotEqual(results[0]["file_id"], results[1]["file_id"])
        self.assertFalse((self.root / "same.txt").exists())
        self.assertEqual(len(list((self.root / "uploads/clean").iterdir())), 2)
        with patch("app.services.storage.scan_file", return_value={"status": "raw_result"}):
            result = self.client.post("/api/files/upload", files={"file": ("test.txt", b"abc")}).json()
        self.assertEqual(result["verdict"], "error")
        self.assertTrue((self.root / "uploads/incoming" / result["file_id"]).exists())

    def test_upload_limits_cleanup_and_empty_file(self):
        with patch("app.services.storage.scan_file") as scanner:
            self.assertEqual(self.client.post("/api/files/upload", files={"file": ("big", b"x" * 129)}).status_code, 413)
            self.assertEqual(self.client.post("/api/files/upload", files={"file": ("empty", b"")}).status_code, 400)
            scanner.assert_not_called()
        self.assertEqual(list((self.root / "uploads/incoming").iterdir()), [])

    def test_total_body_limit_applies_without_trusting_filename(self):
        response = self.client.post("/api/files/upload", content=b"x" * (1024 * 1024 + 129), headers={"Content-Type": "application/octet-stream"})
        self.assertEqual(response.status_code, 413)

    def test_sdk_channel_closed_when_scan_or_json_fails(self):
        for failure in (RuntimeError("secret_exception"), "not-json"):
            sdk = SimpleNamespace(init=Mock(return_value="channel"), scan_file=Mock(), quit=Mock())
            if isinstance(failure, Exception):
                sdk.scan_file.side_effect = failure
            else:
                sdk.scan_file.return_value = failure
            with patch("app.services.file_security.importlib.import_module", return_value=sdk):
                result = file_security.scan_file("path")
            self.assertEqual(result["status"], "error")
            self.assertNotIn("secret_exception", json.dumps(result))
            sdk.quit.assert_called_once_with("channel")

    def test_events_are_concurrent_bounded_and_contain_no_prompt(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _: ai_events.record_ai_event("allowed", "allowed"), range(24)))
        self.assertEqual(ai_events.count_ai_events()["total_ai_events"], 24)
        with ai_events.database() as connection:
            names = [row[1] for row in connection.execute("PRAGMA table_info(ai_events)")]
        self.assertNotIn("prompt", names)
        self.assertNotIn("reply", names)
        with patch.object(ai_events, "settings", replace(ai_events.settings, event_limit=5)):
            ai_events.record_ai_event("allowed", "allowed")
            self.assertEqual(ai_events.count_ai_events()["total_ai_events"], 5)

    def test_legacy_import_is_once_and_contains_no_prompts(self):
        legacy = self.root / "uploads/ai_security_events.json"
        legacy.parent.mkdir()
        legacy.write_text(json.dumps([{"timestamp": datetime.now(timezone.utc).isoformat(), "event_type": "prompt_injection_blocked", "action": "blocked_input_trend", "prompt": "PRIVATE_LEGACY"}]))
        self.assertEqual(ai_events.count_ai_events()["total_ai_events"], 1)
        self.assertEqual(ai_events.count_ai_events()["total_ai_events"], 1)
        with ai_events.database() as connection:
            dump = "\n".join(connection.iterdump())
        self.assertNotIn("PRIVATE_LEGACY", dump)

    def test_invalid_chat_and_provider_failure(self):
        self.assertEqual(self.chat("   ").status_code, 422)
        self.assertEqual(self.chat("x" * 8001).status_code, 422)
        with patch("app.routes.chat.inspect_prompt", return_value=ALLOW), patch("app.routes.chat.get_ai_reply", side_effect=RuntimeError("api-secret")):
            response = self.chat()
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("api-secret", response.text)

    def test_status_unknown_until_external_services_observed(self):
        self.assertEqual(stats.get_portal_stats()["portal_status"], "Pendiente de verificar")
        for name in ("llm", "ai_guard", "file_security"):
            ai_events.set_service_health(name, True)
        self.assertEqual(stats.get_portal_stats()["portal_status"], "Operativo")


if __name__ == "__main__":
    unittest.main()
