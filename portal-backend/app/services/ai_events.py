"""Eventos sin contenido ciudadano; SQLite garantiza escrituras concurrentes."""
from contextlib import contextmanager
import sqlite3
import json
from datetime import datetime
import logging
from time import time

from app.core.config import settings


@contextmanager
def database():
    settings.events_db.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.events_db, timeout=10)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS ai_events (
                id INTEGER PRIMARY KEY, timestamp REAL NOT NULL,
                event_type TEXT NOT NULL, action TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS service_health (
                service TEXT PRIMARY KEY, state TEXT NOT NULL, checked_at REAL NOT NULL
            );
        """)
        with connection:
            migrate_legacy(connection)
            yield connection
    finally:
        connection.close()


def migrate_legacy(connection):
    # Importar una sola vez metadatos recientes; no copiar los prompts antiguos.
    if connection.execute("SELECT 1 FROM metadata WHERE key='legacy_imported'").fetchone():
        return
    connection.execute("BEGIN IMMEDIATE")
    if connection.execute("SELECT 1 FROM metadata WHERE key='legacy_imported'").fetchone():
        return
    legacy = settings.upload_dir / "ai_security_events.json"
    if legacy.exists():
        try:
            if legacy.stat().st_size > 8 * 1024 * 1024:
                raise ValueError("legacy file too large")
            rows = json.loads(legacy.read_text())
            if not isinstance(rows, list):
                raise ValueError("invalid legacy events")
            for event in rows[-settings.event_limit:]:
                if not isinstance(event, dict):
                    continue
                try:
                    timestamp = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00")).timestamp()
                except (KeyError, TypeError, ValueError, AttributeError):
                    continue
                action = {"blocked_input_trend": "blocked_input", "blocked_output_trend": "blocked_output"}.get(event.get("action"))
                kind = event.get("event_type")
                if action and kind in ("trend_guard_blocked", "prompt_injection_blocked", "sensitive_data_request_blocked", "harmful_output_blocked") and timestamp >= time() - settings.event_retention_days * 86400:
                    connection.execute("INSERT INTO ai_events(timestamp,event_type,action) VALUES (?,?,?)", (timestamp, kind, action))
        except (OSError, ValueError):
            logging.getLogger(__name__).warning("legacy_event_import_skipped")
    connection.execute("INSERT OR IGNORE INTO metadata VALUES ('legacy_imported','yes')")


def record_ai_event(event_type: str, action: str):
    with database() as connection:
        connection.execute("INSERT INTO ai_events(timestamp,event_type,action) VALUES (?,?,?)", (time(), event_type, action))
        connection.execute("DELETE FROM ai_events WHERE timestamp < ?", (time() - settings.event_retention_days * 86400,))
        connection.execute("DELETE FROM ai_events WHERE id NOT IN (SELECT id FROM ai_events ORDER BY id DESC LIMIT ?)", (settings.event_limit,))


def set_service_health(service: str, available: bool):
    with database() as connection:
        connection.execute("INSERT OR REPLACE INTO service_health VALUES (?,?,?)", (service, "available" if available else "unavailable", time()))


def get_service_health():
    configured = {"ai_guard": bool(settings.trend_api_key), "llm": bool(settings.openai_api_key), "file_security": bool(settings.file_security_api_key)}
    with database() as connection:
        rows = {name: (state, checked) for name, state, checked in connection.execute("SELECT * FROM service_health")}
    return {name: ("not_configured" if not enabled else rows[name][0] if name in rows and time() - rows[name][1] < 300 else "not_checked") for name, enabled in configured.items()}


def count_ai_events():
    # Totales del intervalo retenido, no contadores vitalicios.
    with database() as connection:
        rows = connection.execute("SELECT event_type, action, COUNT(*) FROM ai_events WHERE timestamp >= ? GROUP BY event_type, action", (time() - settings.event_retention_days * 86400,)).fetchall()
    return {
        "total_ai_events": sum(count for _, _, count in rows),
        "prompt_injection_blocked": sum(count for kind, _, count in rows if kind == "prompt_injection_blocked"),
        "sensitive_data_request_blocked": sum(count for kind, _, count in rows if kind == "sensitive_data_request_blocked"),
        "harmful_output_blocked": sum(count for kind, _, count in rows if kind == "harmful_output_blocked"),
        "trend_guard_blocked": sum(count for _, action, count in rows if action in ("blocked_input", "blocked_output")),
    }
