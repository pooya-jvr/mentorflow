from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class StudentContext(BaseModel):
    technologies: List[str] = Field(default_factory=list)
    current_roadmap: Optional[str] = None
    studied_topics: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str
    level: Optional[str] = "Beginner"
    session_id: Optional[str] = "default"
    context: Optional[StudentContext] = None


class ChatResponse(BaseModel):
    response: str
    tool_used: str
    level: str
    summary: str
    context: StudentContext
    metadata: Dict[str, str] = Field(default_factory=dict)
