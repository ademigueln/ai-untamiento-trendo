"""Proveedor LLM sin persistencia: el orquestador guarda solo respuestas aprobadas."""
from functools import lru_cache
from openai import OpenAI
from app.core.config import settings
from app.services.knowledge_base import get_relevant_context

SYSTEM_PROMPT = """Eres el asistente virtual del AI-untamiento de Trendo, una sede municipal de demostración.
Ayuda con trámites, documentación y servicios digitales. Responde en español, de forma clara y formal.
No inventes normativas ni datos de expedientes: no tienes acceso a expedientes reales.
Usa el contexto municipal disponible y, si falta información, dilo y orienta al ciudadano sobre el siguiente paso.
"""


@lru_cache(maxsize=1)
def get_client():
    return OpenAI(api_key=settings.openai_api_key, timeout=settings.request_timeout, max_retries=1)


def get_ai_reply(message: str, history: list[dict]) -> str:
    if not settings.openai_api_key:
        raise RuntimeError("Proveedor LLM no configurado")
    response = get_client().chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "system", "content": f"Contexto municipal:\n{get_relevant_context(message)}"},
                  *history, {"role": "user", "content": message}],
        temperature=0.3, max_completion_tokens=1000,
    )
    reply = response.choices[0].message.content
    if not reply:
        raise RuntimeError("Respuesta LLM vacía")
    return reply
