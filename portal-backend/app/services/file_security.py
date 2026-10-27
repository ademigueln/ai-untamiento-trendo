"""Adaptador del scanner: ningún formato desconocido constituye un resultado limpio."""
import importlib
import json
import logging
from app.core.config import settings
from app.services.ai_events import set_service_health

logger = logging.getLogger(__name__)


def scan_file(file_path: str) -> dict:
    channel = None
    sdk = None
    try:
        sdk = importlib.import_module("amaas.grpc")
        channel = sdk.init(settings.file_security_host, api_key=settings.file_security_api_key, enable_tls=settings.file_security_tls)
        result = sdk.scan_file(channel, file_path, tags=["trendo-demo"], verbose=True)
        parsed = json.loads(result) if isinstance(result, (str, bytes)) else result
        if not isinstance(parsed, dict):
            raise ValueError("Invalid scan response")
        return parsed
    except Exception:
        logger.warning("file_scan_unavailable")
        set_service_health("file_security", False)
        return {"status": "error", "details": "No se ha podido completar el análisis."}
    finally:
        if channel is not None:
            try:
                sdk.quit(channel)
            except Exception:
                logger.warning("file_scan_channel_close_failed")
