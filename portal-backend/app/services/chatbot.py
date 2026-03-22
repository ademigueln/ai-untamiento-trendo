import os
from dotenv import load_dotenv
from openai import OpenAI

from app.services.knowledge_base import get_relevant_context
from app.services.memory import add_message, get_recent_messages

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
Eres el asistente virtual oficial del AI-untamiento de Trendo.

Tu función es ayudar a la ciudadanía con:
- trámites municipales
- documentación administrativa
- consulta de expedientes
- orientación sobre servicios digitales

Instrucciones:
- responde siempre en español
- sé claro, formal y útil
- no inventes normativas concretas si no las conoces
- si no sabes un dato exacto, dilo claramente
- usa el contexto documental proporcionado cuando esté disponible
- orienta al ciudadano sobre el siguiente paso práctico
- mantén un tono institucional, parecido al de una sede electrónica española
"""


def get_ai_reply(message: str) -> str:
    if not os.getenv("OPENAI_API_KEY"):
        return "Falta configurar la API key de OpenAI en el backend."

    relevant_context = get_relevant_context(message)
    recent_messages = get_recent_messages(limit=6)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": f"Contexto documental municipal disponible:\n\n{relevant_context}",
        },
    ]

    messages.extend(recent_messages)
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3,
    )

    reply = response.choices[0].message.content or "No se ha podido generar una respuesta."

    add_message("user", message)
    add_message("assistant", reply)

    return reply