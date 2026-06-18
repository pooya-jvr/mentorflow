from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.agents.router import detect_tool
from app.services.context import context_store, extract_topic
from app.services.tools import (
    context7_docs,
    create_learning_roadmap,
    find_youtube_videos,
    general_tutor,
    generate_code,
    generate_quiz,
    review_github_repository,
)
from app.services.langchain_agent import run_langchain_agent

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or "default"
    state = context_store.update(session_id, request.level, request.message, request.context)
    tool = detect_tool(request.message)
    topic = extract_topic(request.message)

    if tool == "quiz_generator":
        response = generate_quiz(topic, state.level, state.context)
        metadata = {}
    elif tool == "code_generator":
        response = generate_code(topic, state.level, state.context)
        metadata = {}
    elif tool == "github_review":
        response, metadata = await review_github_repository(request.message, state.level)
    elif tool == "learning_roadmap":
        response = create_learning_roadmap(topic, state.level, state.context)
        state.context.current_roadmap = topic
        metadata = {}
    elif tool == "youtube_search":
        response = find_youtube_videos(topic, state.level)
        metadata = {}
    elif tool == "context7_docs":
        response = context7_docs(topic)
        metadata = {}
    else:
        response = general_tutor(topic, state.level, state.context)
        metadata = {}

    response, langchain_metadata = await run_langchain_agent(
        message=request.message,
        tool=tool,
        tool_output=response,
        level=state.level,
        context=state.context,
        summary=state.summary,
    )
    metadata.update(langchain_metadata)

    return ChatResponse(
        response=response,
        tool_used=tool,
        level=state.level,
        summary=state.summary,
        context=state.context,
        metadata=metadata,
    )
