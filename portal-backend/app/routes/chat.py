from fastapi import APIRouter
from pydantic import BaseModel
from app.services.chatbot import get_ai_reply
from app.services.ai_guard import inspect_prompt, inspect_output

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("")
def chat(request: ChatRequest):
     # -------------------------------------------------------------------
    # Punto de entrada del flujo conversacional.
    # Aquí recibimos el mensaje del usuario desde el frontend.
    # -------------------------------------------------------------------
    print(f"[CHAT] Mensaje recibido: {request.message}")

# -------------------------------------------------------------------
    # 1. Validación de entrada con Trend AI Guard.
    # Antes de llamar al modelo, se analiza el prompt del usuario para
    # detectar prompt injection, contenido dañino o peticiones no deseadas.
    #
    # Esta llamada delega en:
    # - inspect_prompt(...)  -> ai_guard.py
    # - call_trend_ai_guard(...) -> requests.post(...) a Trend
    # -------------------------------------------------------------------

    prompt_check = inspect_prompt(request.message)
    print(f"[CHAT] prompt_check={prompt_check}")

    # -------------------------------------------------------------------
    # Si Trend AI Guard decide bloquear la entrada, no se llama al modelo.
    # El flujo se corta aquí y devolvemos una respuesta controlada al frontend.
    # -------------------------------------------------------------------
    if not prompt_check["allowed"]:
        return {
            "reply": "Solicitud bloqueada por Trend AI Guard.",
            "guard_action": "blocked_input",
            "guard_reason": prompt_check["reason"],
            "guard_source": prompt_check.get("source"),
            "prompt_guard_result": prompt_check.get("trend_result"),
            "output_guard_result": None,
        }
        
# -------------------------------------------------------------------
    # 2. Llamada al modelo LLM.
    # Solo se ejecuta si el prompt ha sido permitido por Trend.
    #
    # Esta llamada delega en:
    # - get_ai_reply(...) -> chatbot.py
    # -------------------------------------------------------------------
    reply = get_ai_reply(request.message)
    print(f"[CHAT] reply modelo={reply}")
    # -------------------------------------------------------------------
    # 3. Validación de salida con Trend AI Guard.
    # Una vez generado el texto por el modelo, se vuelve a evaluar con Trend
    # para decidir si la respuesta puede salir al usuario final.
    #
    # Esta llamada delega en:
    # - inspect_output(prompt, reply) -> ai_guard.py
    # - call_trend_ai_guard(reply, "output")
    # -------------------------------------------------------------------
    output_check = inspect_output(request.message, reply)
    print(f"[CHAT] output_check={output_check}")
    # -------------------------------------------------------------------
    # Si Trend bloquea la salida, no devolvemos el texto generado por el modelo.
    # En su lugar devolvemos una respuesta controlada indicando bloqueo.
    # -------------------------------------------------------------------
    if not output_check["allowed"]:
        return {
            "reply": "La respuesta generada ha sido bloqueada por Trend AI Guard.",
            "guard_action": "blocked_output",
            "guard_reason": output_check["reason"],
            "guard_source": output_check.get("source"),
            "prompt_guard_result": prompt_check.get("trend_result"),
            "output_guard_result": output_check.get("trend_result"),
        }
    # -------------------------------------------------------------------
    # Flujo permitido de extremo a extremo:
    # - prompt permitido
    # - respuesta permitida
    # Se devuelve la respuesta final junto con metadatos de control.
    # -------------------------------------------------------------------
    return {
        "reply": reply,
        "guard_action": "allowed",
        "guard_reason": None,
        "guard_source": output_check.get("source", prompt_check.get("source")),
        "prompt_guard_result": prompt_check.get("trend_result"),
        "output_guard_result": output_check.get("trend_result"),
    }