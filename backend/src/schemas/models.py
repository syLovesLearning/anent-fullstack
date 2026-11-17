"""跨层共享 Pydantic v2 契约模型（对标前端 TypeScript Interface）。"""

from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field


class AuthContext(BaseModel):
    user_id: UUID
    username: str
    role: Literal["admin", "user", "readonly", "external_guest"] = "user"
    allowed_tools: list[str] = Field(default_factory=lambda: ["rag_search"])
    groups: list[str] = Field(default_factory=lambda: ["public"])


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str = ""
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None


class AgentState(BaseModel):
    run_id: UUID
    session_id: UUID
    user_id: UUID
    messages: list[ChatMessage] = Field(default_factory=list)
    step_count: int = 0
    max_steps: int = 6
    total_tokens: int = 0


class SSEEvent(BaseModel):
    event: Literal["thought", "tool_start", "tool_result", "citations", "action_cards", "approval_required", "token", "error", "done"]
    data: dict[str, Any] = Field(default_factory=dict)


class DevLoginRequest(BaseModel):
    username: str = "shenyang"
    role: Literal["admin", "user", "readonly", "external_guest"] = "admin"
    groups: list[str] | None = None


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=4, max_length=128)
    role: Literal["admin", "user", "readonly", "external_guest"] = "user"
    groups: list[str] = Field(default_factory=lambda: ["public"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class SessionCreate(BaseModel):
    agent_name: str = "default"
    title: str = "新对话"


class SessionUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    max_steps: int = Field(default=6, ge=1, le=12)
    top_k: int = Field(default=3, ge=1, le=10)
    min_score: float = Field(default=0.2, ge=0.0, le=1.0)
    enable_rag: bool = True


class MemoryCreate(BaseModel):
    memory_type: Literal["fact", "preference", "summary"] = "fact"
    content: str = Field(min_length=1, max_length=2000)
    importance: int = Field(default=3, ge=1, le=5)
