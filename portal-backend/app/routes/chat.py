from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field, field_validator
from app.services.chatbot import get_ai_reply
from app.services.ai_guard import inspect_prompt, inspect_output, guard_connection
from app.services.ai_events import record_ai_event, set_service_health
from app.services.memory import conversation, add_exchange, clear_memory

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{43}$")

    @field_validator("message")
    @classmethod
    def meaningful(cls, value):
        if not value.strip():
            raise ValueError("Escribe una consulta")
        return value.strip()


@router.post("")
def chat(request: ChatRequest, response: Response):
    with conversation(request.conversation_id) as (token, history), guard_connection():
        prompt_check = inspect_prompt(request.message)
        output_check = None
        action = "allowed"
        check = prompt_check
        if not prompt_check["allowed"]:
            action = "unavailable" if check["source"] == "trend_unavailable" else "blocked_input"
            reply = "La protección del chat no está disponible. Inténtalo más tarde." if action == "unavailable" else "Solicitud bloqueada por Trend AI Guard."
        else:
            try:
                reply = get_ai_reply(request.message, history)
            except Exception:
                set_service_health("llm", False)
                record_ai_event("llm_unavailable", "unavailable")
                raise HTTPException(503, "El servicio de IA no está disponible. Inténtalo más tarde.") from None
            set_service_health("llm", True)
            output_check = inspect_output(request.message, reply)
            check = output_check
            if not output_check["allowed"]:
                action = "unavailable" if check["source"] == "trend_unavailable" else "blocked_output"
                reply = "No se ha podido validar la respuesta. Inténtalo más tarde." if action == "unavailable" else "La respuesta generada ha sido bloqueada por Trend AI Guard."
            elif any(c["source"] == "trend_unavailable" for c in (prompt_check, output_check)):
                action = "degraded"
                check = {"source": "trend_unavailable", "reason": "Respuesta sin todas las comprobaciones de seguridad."}
            else:
                add_exchange(token, request.message, reply)
        record_ai_event(check.get("event_type", "allowed") if action != "allowed" else "allowed", action)
        if action == "unavailable":
            response.status_code = 503
        return {"reply": reply, "conversation_id": token, "guard_action": action,
                "guard_reason": check.get("reason"), "guard_source": check["source"]}


@router.delete("/{token}", status_code=204)
def delete_conversation(token: str):
    clear_memory(token)
