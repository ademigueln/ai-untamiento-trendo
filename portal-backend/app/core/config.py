"""Configuración del portal, independiente del directorio de ejecución."""
from dataclasses import dataclass
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    upload_dir: Path = Path(os.getenv("UPLOAD_DIR", ROOT / "data/uploads"))
    events_db: Path = Path(os.getenv("EVENTS_DB", Path(os.getenv("UPLOAD_DIR", ROOT / "data/uploads")) / "events.sqlite3"))
    knowledge_dir: Path = ROOT / "app/data"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    trend_api_key: str = os.getenv("TREND_API_KEY", "")
    trend_ai_url: str = os.getenv("TREND_AI_URL", "https://api.eu.xdr.trendmicro.com/v3.0/aiSecurity/applyGuardrails")
    trend_ai_app_name: str = os.getenv("TREND_AI_APP_NAME", "ai-untamiento-trendo")
    guard_fail_open: bool = os.getenv("GUARD_FAIL_OPEN", "false").lower() == "true"
    file_security_host: str = os.getenv("FILE_SECURITY_HOST", "my-release-visionone-filesecurity-scanner.visionone-filesecurity.svc.cluster.local:50051")
    file_security_api_key: str = os.getenv("FILE_SECURITY_API_KEY", "")
    file_security_tls: bool = os.getenv("FILE_SECURITY_TLS", "false").lower() == "true"
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))
    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    session_ttl: int = int(os.getenv("SESSION_TTL_SECONDS", "1800"))
    session_limit: int = int(os.getenv("SESSION_LIMIT", "500"))
    history_limit: int = 6
    event_retention_days: int = int(os.getenv("EVENT_RETENTION_DAYS", "7"))
    event_limit: int = 10000
    cors_origins: tuple = tuple(filter(None, os.getenv("CORS_ORIGINS", "").split(",")))


settings = Settings()
