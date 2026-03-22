from fastapi import APIRouter
from pydantic import BaseModel
from app.services.chatbot import get_ai_reply

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("")
def chat(request: ChatRequest):
    reply = get_ai_reply(request.message)
    return {"reply": reply}