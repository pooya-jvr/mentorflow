from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    level: Optional[str] = "Beginner"


class ChatResponse(BaseModel):
    response: str
    tool_used: str