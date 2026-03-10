from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


@router.post("/message")
async def send_message(request: ChatRequest):
    """Send a message and receive an AI-generated reply."""
    return {"reply": "Chatbot endpoint – integrate OpenAI here"}
