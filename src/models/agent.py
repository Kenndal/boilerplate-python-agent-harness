from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import ConfigDict, Field

from src.models.base import BaseAudit, BaseModelWithConfig


class AgentRole(StrEnum):
    user = "user"
    assistant = "assistant"
    system = "system"
    tool_call = "tool_call"
    tool_return = "tool_return"


class AgentMessageCreate(BaseModelWithConfig):
    """Internal write model used when persisting a turn.

    `tool_payload` carries the tool arguments for `tool_call` roles and the tool result for
    `tool_return` roles; it is `None` for plain text turns.  Token counts are persisted for
    observability only and are never surfaced on the public API.
    """

    session_id: UUID
    sequence: int
    role: AgentRole
    content: str
    tool_name: str | None = None
    tool_call_id: str | None = None
    tool_payload: dict[str, Any] | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class AgentMessageUpdate(BaseModelWithConfig):
    is_active: bool = True


class AgentMessage(BaseModelWithConfig, BaseAudit):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    sequence: int
    role: AgentRole
    content: str
    tool_name: str | None = None
    tool_call_id: str | None = None
    tool_payload: dict[str, Any] | None = None
    is_active: bool


class AgentPromptRequest(BaseModelWithConfig):
    prompt: str = Field(min_length=1)


class AgentTurnResponse(BaseModelWithConfig):
    """Response body for `POST /agents/sessions/{id}/messages`.

    Only the assistant-visible output and the freshly-persisted turn records are returned.
    Usage statistics (token counts) are intentionally omitted from the public surface.
    """

    output: str
    new_messages: list[AgentMessage]


__all__ = [
    "AgentMessage",
    "AgentMessageCreate",
    "AgentMessageUpdate",
    "AgentPromptRequest",
    "AgentRole",
    "AgentTurnResponse",
]
