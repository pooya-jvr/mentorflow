from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.agents.router import detect_tool

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    tool = detect_tool(request.message)

    return ChatResponse(
        response=f"Tool detected: {tool}. Student level: {request.level}. Message: {request.message}",
        tool_used=tool,
    )