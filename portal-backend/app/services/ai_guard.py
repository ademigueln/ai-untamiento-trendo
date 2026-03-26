import os
import requests
from app.services.ai_events import record_ai_event

TREND_AI_URL = os.getenv(
    "TREND_AI_URL",
    "https://api.eu.xdr.trendmicro.com/v3.0/aiSecurity/applyGuardrails"
)

TREND_API_KEY = os.getenv("TREND_API_KEY")
TREND_AI_APP_NAME = os.getenv("TREND_AI_APP_NAME", "ai-untamiento-trendo")

# -------------------------------------------------------------------
# Este módulo encapsula TODA la integración con Trend AI Guard.
# El resto del backend no debería construir directamente llamadas HTTP
# a Trend, sino apoyarse en estas funciones de servicio.
# -------------------------------------------------------------------

def call_trend_ai_guard(text: str, direction: str) -> dict:

# -------------------------------------------------------------------
    # Llamada REST real al endpoint de Trend AI Guard.
    #
    # Parámetros:
    # - text: contenido a analizar
    # - direction: "input" o "output"
    #
    # Aunque el parámetro direction se registra y se usa a nivel lógico
    # en la aplicación, el payload actual que se envía a Trend contiene
    # únicamente el campo "prompt".
    # -------------------------------------------------------------------

    print(f"[AI_GUARD] call_trend_ai_guard() direction={direction}")
    print(f"[AI_GUARD] URL={TREND_AI_URL}")
    print(f"[AI_GUARD] APP_NAME={TREND_AI_APP_NAME}")

    if not TREND_API_KEY:
        print("[AI_GUARD] ERROR: falta TREND_API_KEY")
        return {
            "status": "error",
            "details": "Falta TREND_API_KEY"
        }

    headers = {
        "Authorization": f"Bearer {TREND_API_KEY}",
        "TMV1-Application-Name": TREND_AI_APP_NAME,
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    payload = {
        "prompt": text
    }

    try:
        response = requests.post(
            TREND_AI_URL,
            headers=headers,
            json=payload,
            timeout=20
        )

        print(f"[AI_GUARD] HTTP status={response.status_code}")
        print(f"[AI_GUARD] Response text={response.text}")

        if response.status_code >= 300:
            return {
                "status": "error",
                "details": f"HTTP {response.status_code}: {response.text}"
            }

        data = response.json()
        print(f"[AI_GUARD] Response JSON={data}")

        return {
            "status": "ok",
            "result": data
        }

    except Exception as e:
        print(f"[AI_GUARD] EXCEPTION={str(e)}")
        return {
            "status": "error",
            "details": str(e)
        }


def _classify_trend_result(result: dict) -> dict:

 # -------------------------------------------------------------------
    # Esta función traduce la respuesta de Trend a una estructura interna
    # más simple para la aplicación:
    # - allowed / not allowed
    # - reason
    # - tipo de evento interno
    #
    # Aquí también se decide qué tipo de evento registrar en función de
    # los reasons devueltos por Trend.
    # -------------------------------------------------------------------

    action = result.get("action", "Allow")
    reasons = result.get("reasons", [])

    if action == "Block":
        reason_text = ", ".join(reasons) if reasons else "Blocked by Trend AI Guard"

        event_type = "trend_guard_blocked"

        if any("prompt" in r.lower() for r in reasons):
            event_type = "prompt_injection_blocked"
        elif any("sensitive" in r.lower() for r in reasons):
            event_type = "sensitive_data_request_blocked"
        elif any("harmful" in r.lower() for r in reasons):
            event_type = "harmful_output_blocked"

        return {
            "allowed": False,
            "reason": reason_text,
            "event_type": event_type,
        }

    return {
        "allowed": True,
        "reason": None,
        "event_type": None,
    }


def inspect_prompt(prompt: str) -> dict:

# -------------------------------------------------------------------
    # Validación del prompt de entrada.
    #
    # Flujo:
    # 1. llama a Trend
    # 2. si Trend falla, la aplicación no bloquea por defecto
    #    y marca source=trend_unavailable
    # 3. si Trend responde correctamente, clasifica el resultado
    # 4. si está bloqueado, registra evento en ai_events.py
    # -------------------------------------------------------------------

    trend_result = call_trend_ai_guard(prompt, "input")

    if trend_result.get("status") != "ok":
        return {
            "allowed": True,
            "reason": None,
            "source": "trend_unavailable",
            "trend_result": trend_result,
        }

    parsed = _classify_trend_result(trend_result["result"])

    if not parsed["allowed"]:
        record_ai_event(
            event_type=parsed["event_type"],
            prompt=prompt,
            action="blocked_input_trend",
            details=parsed["reason"] or "",
        )

    return {
        "allowed": parsed["allowed"],
        "reason": parsed["reason"],
        "source": "trend_ai_guard",
        "trend_result": trend_result,
    }


def inspect_output(prompt: str, output_text: str) -> dict:

# -------------------------------------------------------------------
    # Validación de la salida generada por el modelo.
    #
    # Flujo:
    # 1. llama a Trend con el texto de salida
    # 2. si Trend no está disponible, no bloquea por defecto
    # 3. si Trend responde "Block", registra evento y devuelve bloqueo
    # -------------------------------------------------------------------

    trend_result = call_trend_ai_guard(output_text, "output")

    if trend_result.get("status") != "ok":
        return {
            "allowed": True,
            "reason": None,
            "source": "trend_unavailable",
            "trend_result": trend_result,
        }

    parsed = _classify_trend_result(trend_result["result"])

    if not parsed["allowed"]:
        record_ai_event(
            event_type=parsed["event_type"],
            prompt=prompt,
            action="blocked_output_trend",
            details=parsed["reason"] or "",
        )

    return {
        "allowed": parsed["allowed"],
        "reason": parsed["reason"],
        "source": "trend_ai_guard",
        "trend_result": trend_result,
    }