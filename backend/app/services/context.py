from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from app.schemas.chat import StudentContext


KNOWN_TECHNOLOGIES = [
    "React",
    "Next.js",
    "FastAPI",
    "Django",
    "Python",
    "JavaScript",
    "TypeScript",
    "Node.js",
    "PostgreSQL",
    "Docker",
    "LangChain",
    "GitHub",
]


@dataclass
class ConversationState:
    level: str = "Beginner"
    context: StudentContext = field(default_factory=StudentContext)
    turns: List[str] = field(default_factory=list)
    summary: str = ""


class ContextStore:
    def __init__(self) -> None:
        self._sessions: Dict[str, ConversationState] = {}

    def get(self, session_id: str) -> ConversationState:
        return self._sessions.setdefault(session_id, ConversationState())

    def update(self, session_id: str, level: str, message: str, context: StudentContext | None) -> ConversationState:
        state = self.get(session_id)
        state.level = normalize_level(level)

        if context:
            state.context.technologies = merge_unique(state.context.technologies, context.technologies)
            state.context.studied_topics = merge_unique(state.context.studied_topics, context.studied_topics)
            state.context.current_roadmap = context.current_roadmap or state.context.current_roadmap

        detected_tech = [tech for tech in KNOWN_TECHNOLOGIES if re.search(rf"\b{re.escape(tech)}\b", message, re.I)]
        state.context.technologies = merge_unique(state.context.technologies, detected_tech)

        topic = extract_topic(message)
        if topic:
            state.context.studied_topics = merge_unique(state.context.studied_topics, [topic])

        state.turns.append(f"{state.level}: {message.strip()}")
        if len(state.turns) > 8:
            compacted = state.turns[:-6]
            state.summary = summarize_turns(state.summary, compacted)
            state.turns = state.turns[-6:]

        return state


def normalize_level(level: str | None) -> str:
    value = (level or "Beginner").strip().lower()
    if value.startswith("adv"):
        return "Advanced"
    if value.startswith("inter"):
        return "Intermediate"
    return "Beginner"


def merge_unique(current: List[str], incoming: List[str]) -> List[str]:
    seen = {item.lower() for item in current}
    merged = list(current)
    for item in incoming:
        clean = item.strip()
        if clean and clean.lower() not in seen:
            merged.append(clean)
            seen.add(clean.lower())
    return merged


def extract_topic(message: str) -> str:
    patterns = [
        r"(?:about|for|چیست|درباره|برای)\s+(.+)$",
        r"(?:what is|explain|generate|create|review)\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, message.strip(), re.I)
        if match:
            return match.group(1).strip(" ?.")
    return message.strip(" ?.")[:80]


def summarize_turns(previous_summary: str, turns: List[str]) -> str:
    topics = [extract_topic(turn) for turn in turns if turn.strip()]
    compact = "; ".join(topics[-5:])
    if not compact:
        return previous_summary
    if previous_summary:
        return f"{previous_summary} | Earlier topics: {compact}"
    return f"Earlier topics: {compact}"


context_store = ContextStore()
