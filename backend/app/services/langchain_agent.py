from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Tuple

from pydantic import BaseModel, Field

from app.agents.router import detect_tool
from app.schemas.chat import StudentContext
from app.services.context import extract_topic
from app.services.tools import (
    context7_docs,
    create_learning_roadmap,
    extract_github_url,
    find_youtube_videos,
    general_tutor,
    generate_code,
    generate_quiz,
    parse_owner_repo,
    review_github_repository,
)

try:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnableLambda
    from langchain_core.tools import StructuredTool
except ImportError:  # pragma: no cover - dependency guard for partial installs
    ChatPromptTemplate = None
    RunnableLambda = None
    StrOutputParser = None
    StructuredTool = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - optional until provider is configured
    ChatOpenAI = None


class ToolChoice(BaseModel):
    tool: str = Field(
        description=(
            "One of quiz_generator, code_generator, github_review, "
            "learning_roadmap, youtube_search, context7_docs, general_tutor."
        )
    )
    topic: str = Field(description="The topic or repository URL to pass to the tool.")


class TutorToolArgs(BaseModel):
    topic: str = Field(description="Topic, technology, learning goal, or repository URL.")
    level: str = Field(description="Student level: Beginner, Intermediate, or Advanced.")


SYSTEM_PROMPT = """You are MentorFlow, an intelligent programming education assistant.
Answer in Persian unless the user clearly asks for another language.
Adapt the response to the student level:
- Beginner: simple language, small steps, concrete examples.
- Intermediate: practical patterns, trade-offs, and exercises.
- Advanced: lifecycle, architecture, edge cases, testing, performance, and production concerns.

Available tools:
- quiz_generator: generate quizzes.
- code_generator: generate code and educational examples.
- github_review: review GitHub repositories.
- learning_roadmap: create personalized learning paths.
- youtube_search: find related educational videos.
- context7_docs: point to current documentation.
- general_tutor: explain general programming questions.

Use the tool output as grounded context. Do not invent GitHub facts beyond the tool output."""


def _metadata() -> Dict[str, str]:
    return {
        "agent": "langchain",
        "model": os.getenv("MENTORFLOW_MODEL", "gpt-4o-mini"),
        "base_url": os.getenv("MENTORFLOW_BASE_URL", "https://api.openai.com/v1"),
    }


def _llm() -> Any | None:
    if not os.getenv("OPENAI_API_KEY") or ChatOpenAI is None:
        return None
    return ChatOpenAI(
        model=os.getenv("MENTORFLOW_MODEL", "gpt-4o-mini"),
        base_url=os.getenv("MENTORFLOW_BASE_URL", "https://api.openai.com/v1"),
        temperature=0.2,
        timeout=20,
        max_retries=1,
    )


def _requires_llm_response() -> bool:
    if not os.getenv("OPENAI_API_KEY"):
        return False
    return os.getenv("MENTORFLOW_REQUIRE_LLM", "true").strip().lower() not in {"0", "false", "no"}


def _uses_llm_router() -> bool:
    return os.getenv("MENTORFLOW_LLM_ROUTER", "false").strip().lower() in {"1", "true", "yes"}


def _safe_provider_message(exc: Exception) -> str:
    message = str(exc)
    message = re.sub(r"(api[_-]?key['\"]?\s*[:=]\s*['\"]?)[^,'\"\s}]+", r"\1***", message, flags=re.I)
    message = re.sub(r"(Bearer\s+)[A-Za-z0-9._-]+", r"\1***", message)
    return message[:700]


def _exception_metadata(exc: Exception, prefix: str) -> Dict[str, str]:
    data = {
        f"{prefix}_error": exc.__class__.__name__,
        f"{prefix}_message": _safe_provider_message(exc),
    }
    status_code = getattr(exc, "status_code", None)
    if status_code is not None:
        data[f"{prefix}_status_code"] = str(status_code)
    response = getattr(exc, "response", None)
    if response is not None and getattr(response, "status_code", None) is not None:
        data[f"{prefix}_status_code"] = str(response.status_code)
    return data


def _provider_error_response(metadata: Dict[str, str]) -> str:
    model = metadata.get("model", "configured model")
    base_url = metadata.get("base_url", "configured provider")
    error = metadata.get("response_error") or metadata.get("router_error") or "ProviderError"
    status = metadata.get("response_status_code") or metadata.get("router_status_code")
    provider_message = metadata.get("response_message") or metadata.get("router_message")
    return (
        "پاسخ آماده برنمی‌گردانم چون حالت AI واقعی فعال است، "
        "اما مدل هوش مصنوعی الان جواب نداد.\n\n"
        f"- Provider: `{base_url}`\n"
        f"- Model: `{model}`\n"
        f"- Error: `{error}`\n\n"
        + (f"- Status: `{status}`\n" if status else "")
        + (f"- Provider message: `{provider_message}`\n\n" if provider_message else "\n")
        + "این پیام از خود provider آمده است. بعد از درست شدن provider، همین endpoint پاسخ واقعی مدل را برمی‌گرداند."
    )


def _tool_context(context: StudentContext) -> str:
    return json.dumps(
        {
            "technologies": context.technologies,
            "current_roadmap": context.current_roadmap,
            "studied_topics": context.studied_topics[-8:],
        },
        ensure_ascii=False,
    )


def _build_langchain_tools(context: StudentContext, original_message: str) -> Dict[str, Any]:
    if StructuredTool is None:
        return {}

    def quiz_generator_tool(topic: str, level: str) -> str:
        return generate_quiz(topic, level, context)

    def code_generator_tool(topic: str, level: str) -> str:
        return generate_code(topic, level, context)

    async def github_review_tool(topic: str, level: str) -> str:
        output, _ = await review_github_repository(original_message or topic, level)
        return output

    def learning_roadmap_tool(topic: str, level: str) -> str:
        context.current_roadmap = topic
        return create_learning_roadmap(topic, level, context)

    def youtube_search_tool(topic: str, level: str) -> str:
        return find_youtube_videos(topic, level)

    def context7_docs_tool(topic: str, level: str) -> str:
        return context7_docs(topic)

    def general_tutor_tool(topic: str, level: str) -> str:
        return general_tutor(topic, level, context)

    tools = [
        StructuredTool.from_function(
            quiz_generator_tool,
            name="quiz_generator",
            description="Generate a quiz for a programming topic.",
            args_schema=TutorToolArgs,
        ),
        StructuredTool.from_function(
            code_generator_tool,
            name="code_generator",
            description="Generate educational code examples.",
            args_schema=TutorToolArgs,
        ),
        StructuredTool.from_function(
            coroutine=github_review_tool,
            name="github_review",
            description="Review a GitHub repository and provide educational feedback.",
            args_schema=TutorToolArgs,
        ),
        StructuredTool.from_function(
            learning_roadmap_tool,
            name="learning_roadmap",
            description="Create a personalized programming learning roadmap.",
            args_schema=TutorToolArgs,
        ),
        StructuredTool.from_function(
            youtube_search_tool,
            name="youtube_search",
            description="Find educational YouTube search results for a topic.",
            args_schema=TutorToolArgs,
        ),
        StructuredTool.from_function(
            context7_docs_tool,
            name="context7_docs",
            description="Find current documentation links through Context7.",
            args_schema=TutorToolArgs,
        ),
        StructuredTool.from_function(
            general_tutor_tool,
            name="general_tutor",
            description="Explain a general programming concept.",
            args_schema=TutorToolArgs,
        ),
    ]
    return {item.name: item for item in tools}


async def run_mentor_agent(
    *,
    message: str,
    level: str,
    context: StudentContext,
    summary: str,
) -> Tuple[str, str, Dict[str, str]]:
    """LangChain-first mentor agent.

    The endpoint delegates tool selection, tool execution, and final response
    shaping here. When a provider key and credit are available, ChatOpenAI uses
    LangChain tool calling. Without provider access, a LangChain fallback router
    keeps local development working.
    """

    metadata = _metadata()
    tool, topic = await _select_tool_with_langchain(message, level, context, summary, metadata)
    tool_output, tool_metadata = await _execute_tool(tool, topic, level, context, message)
    metadata.update(tool_metadata)
    response = await _finalize_with_langchain(message, level, context, summary, tool, tool_output, metadata)
    return response, tool, metadata


async def _select_tool_with_langchain(
    message: str,
    level: str,
    context: StudentContext,
    summary: str,
    metadata: Dict[str, str],
) -> tuple[str, str]:
    local_tool = detect_tool(message)
    local_topic = extract_topic(message)

    if ChatPromptTemplate is None or RunnableLambda is None:
        metadata["router_mode"] = "direct_router_missing_langchain"
        return local_tool, local_topic

    llm = _llm() if _uses_llm_router() else None
    if not _uses_llm_router():
        metadata["router_mode"] = "langchain_local_router_metis_direct_mode"

    if llm is not None:
        try:
            router_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", SYSTEM_PROMPT),
                    (
                        "human",
                        """Choose the best MentorFlow tool for this student message.
Return only a tool call.

Student message: {message}
Student level: {level}
Student context: {context}
Conversation summary: {summary}""",
                    ),
                ]
            )
            chooser = llm.bind_tools([ToolChoice], tool_choice="ToolChoice")
            ai_message = await (router_prompt | chooser).ainvoke(
                {
                    "message": message,
                    "level": level,
                    "context": _tool_context(context),
                    "summary": summary or "none",
                }
            )
            if getattr(ai_message, "tool_calls", None):
                args = ai_message.tool_calls[0]["args"]
                metadata["router_mode"] = "langchain_llm_tool_call"
                return args.get("tool", local_tool), args.get("topic", local_topic)
        except Exception as exc:  # provider/network dependent
            metadata["router_mode"] = "langchain_router_fallback_after_llm_error"
            metadata.update(_exception_metadata(exc, "router"))

    fallback_router = RunnableLambda(lambda data: {"tool": detect_tool(data["message"]), "topic": extract_topic(data["message"])})
    choice = await fallback_router.ainvoke({"message": message})
    metadata.setdefault("router_mode", "langchain_local_router")
    return choice["tool"], choice["topic"]


async def _execute_tool(
    tool: str,
    topic: str,
    level: str,
    context: StudentContext,
    original_message: str,
) -> tuple[str, Dict[str, str]]:
    metadata: Dict[str, str] = {"tool_execution": "langchain_structured_tool"}
    registry = _build_langchain_tools(context, original_message)
    selected = registry.get(tool) or registry.get("general_tutor")

    if selected is not None:
        if tool == "github_review":
            output = await selected.ainvoke({"topic": topic, "level": level})
            url = extract_github_url(original_message) or extract_github_url(topic)
            if url:
                metadata["repository"] = parse_owner_repo(url)
            return output, metadata
        output = await selected.ainvoke({"topic": topic, "level": level})
        return str(output), metadata

    metadata["tool_execution"] = "direct_tool_fallback_missing_langchain"
    if tool == "quiz_generator":
        return generate_quiz(topic, level, context), metadata
    if tool == "code_generator":
        return generate_code(topic, level, context), metadata
    if tool == "github_review":
        output, github_metadata = await review_github_repository(original_message, level)
        metadata.update(github_metadata)
        return output, metadata
    if tool == "learning_roadmap":
        context.current_roadmap = topic
        return create_learning_roadmap(topic, level, context), metadata
    if tool == "youtube_search":
        return find_youtube_videos(topic, level), metadata
    if tool == "context7_docs":
        return context7_docs(topic), metadata
    return general_tutor(topic, level, context), metadata


async def _finalize_with_langchain(
    message: str,
    level: str,
    context: StudentContext,
    summary: str,
    tool: str,
    tool_output: str,
    metadata: Dict[str, str],
) -> str:
    if ChatPromptTemplate is None or RunnableLambda is None or StrOutputParser is None:
        metadata["response_mode"] = "direct_tool_output_missing_langchain"
        if _requires_llm_response():
            metadata["response_error"] = "LangChainMissing"
            return _provider_error_response(metadata)
        return tool_output

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                """Student message: {message}
Student level: {level}
Student context: {context}
Conversation summary: {summary}
Selected LangChain tool: {tool}
Tool output:
{tool_output}

Create the final MentorFlow response.""",
            ),
        ]
    )

    chain_input = {
        "message": message,
        "level": level,
        "context": _tool_context(context),
        "summary": summary or "none",
        "tool": tool,
        "tool_output": tool_output,
    }

    llm = _llm()
    if llm is not None:
        try:
            chain = prompt | llm | StrOutputParser()
            metadata["response_mode"] = "langchain_llm_response"
            return await chain.ainvoke(chain_input)
        except Exception as exc:  # provider/network dependent
            metadata["response_mode"] = "langchain_provider_error"
            metadata.update(_exception_metadata(exc, "response"))
            if _requires_llm_response():
                return _provider_error_response(metadata)

    if _requires_llm_response():
        metadata["response_mode"] = "langchain_provider_not_configured"
        metadata["response_error"] = "ProviderNotConfigured"
        return _provider_error_response(metadata)

    fallback_chain = prompt | RunnableLambda(lambda data: data.messages[-1].content.split("Tool output:\n", 1)[-1])
    metadata.setdefault("response_mode", "langchain_local_response")
    return await fallback_chain.ainvoke(chain_input)
