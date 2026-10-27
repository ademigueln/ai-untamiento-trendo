"""Sesiones efímeras de una sola réplica: TTL, capacidad y exclusión por conversación."""
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
import secrets
from threading import RLock
from time import monotonic

from fastapi import HTTPException
from app.core.config import settings


@dataclass
class Conversation:
    messages: deque = field(default_factory=lambda: deque(maxlen=settings.history_limit))
    touched: float = field(default_factory=monotonic)
    busy: bool = False


_sessions: dict[str, Conversation] = {}
_lock = RLock()


def _expire():
    now = monotonic()
    for token, session in list(_sessions.items()):
        if not session.busy and now - session.touched > settings.session_ttl:
            del _sessions[token]


@contextmanager
def conversation(token: str | None):
    with _lock:
        _expire()
        if token is None:
            if len(_sessions) >= settings.session_limit:
                raise HTTPException(503, "Se ha alcanzado el límite de conversaciones. Inténtalo más tarde.")
            token = secrets.token_urlsafe(32)
            _sessions[token] = Conversation()
        session = _sessions.get(token)
        if session is None:
            raise HTTPException(404, "La conversación ha caducado. Inicia una nueva.")
        if session.busy:
            raise HTTPException(409, "La conversación está procesando otra petición.")
        session.busy = True
        history = list(session.messages)
    try:
        yield token, history
    finally:
        with _lock:
            session.busy = False
            session.touched = monotonic()


def add_exchange(token: str, message: str, reply: str):
    with _lock:
        session = _sessions[token]
        session.messages.extend([{"role": "user", "content": message}, {"role": "assistant", "content": reply}])


def clear_memory(token: str):
    with _lock:
        session = _sessions.get(token)
        if session and session.busy:
            raise HTTPException(409, "Espera a que termine la respuesta antes de borrar la conversación.")
        _sessions.pop(token, None)
