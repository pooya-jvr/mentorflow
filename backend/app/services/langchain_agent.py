from __future__ import annotations

import os
from typing import Dict, Tuple

from app.schemas.chat import StudentContext

try:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnableLambda
except ImportError:  # pragma: no cover - dependency guard for partial installs
    ChatPromptTemplate = None
    RunnableLambda = None
    StrOutputParser = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - optional until OPENAI_API_KEY is configured
    ChatOpenAI = None


SYSTEM_PROMPT = """You are MentorFlow, an intelligent programming education assistant.
Answer in Persian unless the user clearly asks for another language.
Adapt the explanation to the student level:
- Beginner: simple language, small steps, concrete examples.
- Intermediate: practical patterns, trade-offs, and exercises.
- Advanced: lifecycle, architecture, edge cases, testing, performance, and production concerns.

Use the selected tool output as grounded context. Do not invent GitHub facts beyond the provided tool output.
Keep the answer educational, actionable, and friendly."""


async def run_langchain_agent(
    *,
    message: str,
    tool: str,
    tool_output: str,
    level: str,
    context: StudentContext,
    summary: str,
) -> Tuple[str, Dict[str, str]]:
    """Run the selected tool output through a LangChain chain.

    With OPENAI_API_KEY and langchain-openai installed, this uses ChatOpenAI.
    Without a key, it still uses a LangChain RunnableLambda so local development
    remains usable and visibly LangChain-powered.
    """

    metadata = {
        "agent": "langchain",
        "tool": tool,
        "model": os.getenv("MENTORFLOW_MODEL", "grok-3-beta"),
        "base_url": os.getenv("MENTORFLOW_BASE_URL", "https://api.openai.com/v1"),
    }

    if ChatPromptTemplate is None or RunnableLambda is None or StrOutputParser is None:
        metadata["mode"] = "direct_fallback_missing_langchain"
        return tool_output, metadata

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                """Student message: {message}
Student level: {level}
Known technologies: {technologies}
Current roadmap: {current_roadmap}
Studied topics: {studied_topics}
Conversation summary: {summary}
Selected tool: {tool}
Tool output:
{tool_output}

Create the final MentorFlow response.""",
            ),
        ]
    )

    chain_input = {
        "message": message,
        "level": level,
        "technologies": ", ".join(context.technologies) or "none",
        "current_roadmap": context.current_roadmap or "none",
        "studied_topics": ", ".join(context.studied_topics[-8:]) or "none",
        "summary": summary or "none",
        "tool": tool,
        "tool_output": tool_output,
    }

    if os.getenv("OPENAI_API_KEY") and ChatOpenAI is not None:
        try:
            model = ChatOpenAI(
                model=metadata["model"],
                base_url=metadata["base_url"],
                temperature=0.2,
                timeout=20,
                max_retries=1,
            )
            chain = prompt | model | StrOutputParser()
            metadata["mode"] = "chat_openai"
            return await chain.ainvoke(chain_input), metadata
        except Exception as exc:  # pragma: no cover - network/provider dependent
            metadata["mode"] = "local_fallback_after_llm_error"
            metadata["error"] = exc.__class__.__name__

    fallback_chain = prompt | RunnableLambda(lambda data: data.messages[-1].content.split("Tool output:\n", 1)[-1])
    metadata.setdefault("mode", "local_langchain_fallback")
    return await fallback_chain.ainvoke(chain_input), metadata
