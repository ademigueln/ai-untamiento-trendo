"""Adaptador AI Guard: contrato explícito y política de indisponibilidad configurable."""
from contextlib import contextmanager
from threading import local
import httpx

from app.core.config import settings
from app.services.ai_events import set_service_health

_local = local()


@contextmanager
def guard_connection():
    # Una conexión reutilizada para las inspecciones de entrada y salida de una petición.
    with httpx.Client(timeout=settings.request_timeout) as client:
        _local.client = client
        try:
            yield
        finally:
            _local.client = None


def call_trend_ai_guard(text: str, direction: str) -> dict:
    # direction identifica la fase local. El contrato REST actual envía "prompt".
    if not settings.trend_api_key:
        return {"status": "error"}
    try:
        client = getattr(_local, "client", None)
        if client is None:
            with guard_connection():
                return call_trend_ai_guard(text, direction)
        response = client.post(settings.trend_ai_url, headers={
            "Authorization": f"Bearer {settings.trend_api_key}",
            "TMV1-Application-Name": settings.trend_ai_app_name,
            "Prefer": "return=representation",
        }, json={"prompt": text})
        response.raise_for_status()
        return {"status": "ok", "result": response.json()}
    except (httpx.HTTPError, ValueError):
        return {"status": "error"}


def _classify_trend_result(result):
    if not isinstance(result, dict) or result.get("action") not in ("Allow", "Block"):
        return None
    reasons = result.get("reasons", [])
    if not isinstance(reasons, list) or not all(isinstance(reason, str) for reason in reasons):
        return None
    kind = "trend_guard_blocked"
    for word, candidate in (("prompt", "prompt_injection_blocked"), ("sensitive", "sensitive_data_request_blocked"), ("harmful", "harmful_output_blocked")):
        if any(word in reason.lower() for reason in reasons):
            kind = candidate
            break
    return {"allowed": result["action"] == "Allow", "reason": ", ".join(reasons)[:500] or "Contenido bloqueado por la política de seguridad.", "event_type": kind}


def _inspect(text, direction):
    result = call_trend_ai_guard(text, direction)
    parsed = _classify_trend_result(result.get("result")) if result.get("status") == "ok" else None
    set_service_health("ai_guard", parsed is not None)
    if parsed is None:
        return {"allowed": settings.guard_fail_open, "reason": "AI Guard no está disponible o devolvió un resultado no válido.", "source": "trend_unavailable", "event_type": "guard_unavailable"}
    return {**parsed, "reason": None if parsed["allowed"] else parsed["reason"], "source": "trend_ai_guard"}


def inspect_prompt(prompt: str):
    return _inspect(prompt, "input")


def inspect_output(prompt: str, output_text: str):
    return _inspect(output_text, "output")
