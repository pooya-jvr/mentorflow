from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.context import context_store
from app.services.langchain_agent import run_mentor_agent

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or "default"
    state = context_store.update(session_id, request.level, request.message, request.context)
    response, tool, metadata = await run_mentor_agent(
        message=request.message,
        level=state.level,
        context=state.context,
        summary=state.summary,
    )

    return ChatResponse(
        response=response,
        tool_used=tool,
        level=state.level,
        summary=state.summary,
        context=state.context,
        metadata=metadata,
    )
