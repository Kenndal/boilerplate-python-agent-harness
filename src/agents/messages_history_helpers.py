"""Bridge between persisted `AgentMessageEntity` rows and pydantic-ai `ModelMessage`s.

Conversations are stored in Postgres as one row per logical turn part so they are queryable
and renderable without instantiating pydantic-ai types.  At runtime we need to feed pydantic-ai
its own `ModelMessage` list, so this module translates in both directions, preserving tool
call / return traces for lossless replay.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
import json
import logging
from typing import Any
from uuid import UUID

from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from src.database.entities.agent_message import AgentMessageEntity
from src.models.agent import AgentMessageCreate, AgentRole

logger = logging.getLogger(__name__)


def rows_to_model_messages(rows: Iterable[AgentMessageEntity]) -> list[ModelMessage]:
    """Reconstruct the pydantic-ai message list from persisted rows.

    Rows of the same logical kind (request vs response) that sit adjacent are coalesced into
    a single `ModelRequest` / `ModelResponse` so the resulting list stays compact and
    faithful to how pydantic-ai would have produced it.  Tool-call rows are grouped into the
    preceding assistant response; tool-return rows are grouped into the next user/system
    request.  Rows with mismatched payload types fall back to a best-effort string content.
    """
    messages: list[ModelMessage] = []
    pending_tool_call_ids: dict[str, list[str]] = {}
    for row in rows:
        role = _safe_role(row.role)
        match role:
            case AgentRole.system:
                messages.append(ModelRequest(parts=[SystemPromptPart(content=row.content)]))
            case AgentRole.user:
                messages.append(ModelRequest(parts=[UserPromptPart(content=row.content)]))
            case AgentRole.assistant:
                _append_response_part(messages, TextPart(content=row.content))
            case AgentRole.tool_call:
                args: Any = row.tool_payload if row.tool_payload is not None else {}
                tool_name = row.tool_name or "unknown_tool"
                tool_call_id = row.tool_call_id or _fallback_tool_call_id(row.sequence)
                pending_tool_call_ids.setdefault(tool_name, []).append(tool_call_id)
                _append_response_part(
                    messages,
                    ToolCallPart(
                        tool_name=tool_name,
                        tool_call_id=tool_call_id,
                        args=args,
                    ),
                )
            case AgentRole.tool_return:
                content = row.tool_payload if row.tool_payload is not None else row.content
                tool_name = row.tool_name or "unknown_tool"
                tool_call_id = row.tool_call_id or _resolve_tool_call_id(
                    pending_tool_call_ids=pending_tool_call_ids,
                    tool_name=tool_name,
                    sequence=row.sequence,
                )
                _append_request_part(
                    messages,
                    ToolReturnPart(
                        tool_name=tool_name,
                        content=content,
                        tool_call_id=tool_call_id,
                    ),
                )
    return messages


def model_messages_to_creates(
    messages: Sequence[ModelMessage],
    session_id: UUID,
    start_sequence: int,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> list[AgentMessageCreate]:
    """Flatten pydantic-ai `ModelMessage`s into persistence-ready `AgentMessageCreate` rows.

    `start_sequence` is the next free sequence number for the session; each returned row
    gets a monotonic `sequence` so the unique `(session_id, sequence)` constraint holds.
    Usage totals are attributed only to the *final* assistant text row - individual tokens
    are not persisted per intermediate tool turn.
    """
    creates: list[AgentMessageCreate] = []
    for msg in messages:
        if isinstance(msg, ModelRequest):
            creates.extend(_request_to_creates(msg, session_id))
        elif isinstance(msg, ModelResponse):
            creates.extend(_response_to_creates(msg, session_id))

    for offset, row in enumerate(creates):
        creates[offset] = row.model_copy(update={"sequence": start_sequence + offset})

    _attach_usage_to_final_assistant(creates, input_tokens, output_tokens)
    return creates


def _safe_role(value: str) -> AgentRole | None:
    try:
        return AgentRole(value)
    except ValueError:
        logger.warning("Encountered unknown agent role %r while replaying history", value)
        return None


def _append_response_part(messages: list[ModelMessage], part: TextPart | ToolCallPart) -> None:
    if messages and isinstance(messages[-1], ModelResponse):
        merged = [*messages[-1].parts, part]
        messages[-1] = ModelResponse(parts=merged)
    else:
        messages.append(ModelResponse(parts=[part]))


def _append_request_part(messages: list[ModelMessage], part: ToolReturnPart) -> None:
    if messages and isinstance(messages[-1], ModelRequest):
        merged = [*messages[-1].parts, part]
        messages[-1] = ModelRequest(parts=merged)
    else:
        messages.append(ModelRequest(parts=[part]))


def _request_to_creates(msg: ModelRequest, session_id: UUID) -> list[AgentMessageCreate]:
    rows: list[AgentMessageCreate] = []
    for part in msg.parts:
        if isinstance(part, SystemPromptPart):
            rows.append(
                AgentMessageCreate(
                    session_id=session_id,
                    sequence=0,
                    role=AgentRole.system,
                    content=part.content,
                )
            )
        elif isinstance(part, UserPromptPart):
            content = part.content if isinstance(part.content, str) else str(part.content)
            rows.append(
                AgentMessageCreate(
                    session_id=session_id,
                    sequence=0,
                    role=AgentRole.user,
                    content=content,
                )
            )
        elif isinstance(part, ToolReturnPart):
            payload = _coerce_jsonable(part.content)
            rows.append(
                AgentMessageCreate(
                    session_id=session_id,
                    sequence=0,
                    role=AgentRole.tool_return,
                    content=_short_summary(payload),
                    tool_name=part.tool_name,
                    tool_call_id=part.tool_call_id,
                    tool_payload=payload if isinstance(payload, dict) else {"value": payload},
                )
            )
    return rows


def _response_to_creates(msg: ModelResponse, session_id: UUID) -> list[AgentMessageCreate]:
    rows: list[AgentMessageCreate] = []
    for part in msg.parts:
        if isinstance(part, TextPart):
            rows.append(
                AgentMessageCreate(
                    session_id=session_id,
                    sequence=0,
                    role=AgentRole.assistant,
                    content=part.content,
                )
            )
        elif isinstance(part, ToolCallPart):
            args = _coerce_tool_args(part.args)
            rows.append(
                AgentMessageCreate(
                    session_id=session_id,
                    sequence=0,
                    role=AgentRole.tool_call,
                    content=f"{part.tool_name}({json.dumps(args, default=str)})",
                    tool_name=part.tool_name,
                    tool_call_id=part.tool_call_id,
                    tool_payload=args,
                )
            )
    return rows


def _attach_usage_to_final_assistant(
    creates: list[AgentMessageCreate],
    input_tokens: int | None,
    output_tokens: int | None,
) -> None:
    if input_tokens is None and output_tokens is None:
        return
    for idx in range(len(creates) - 1, -1, -1):
        if creates[idx].role == AgentRole.assistant:
            creates[idx] = creates[idx].model_copy(
                update={"input_tokens": input_tokens, "output_tokens": output_tokens},
            )
            return


def _coerce_tool_args(args: Any) -> dict[str, Any]:  # noqa: ANN401
    if isinstance(args, dict):
        return args
    if isinstance(args, str):
        try:
            decoded = json.loads(args)
        except json.JSONDecodeError:
            return {"_raw": args}
        return decoded if isinstance(decoded, dict) else {"value": decoded}
    return {"value": _coerce_jsonable(args)}


def _coerce_jsonable(value: Any) -> Any:  # noqa: ANN401
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, dict)):
        return value
    return str(value)


def _short_summary(value: Any) -> str:  # noqa: ANN401
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, default=str)[:1024]
    except (TypeError, ValueError):
        return str(value)[:1024]


def _resolve_tool_call_id(pending_tool_call_ids: dict[str, list[str]], tool_name: str, sequence: int) -> str:
    ids = pending_tool_call_ids.get(tool_name)
    if ids:
        return ids.pop(0)
    return _fallback_tool_call_id(sequence)


def _fallback_tool_call_id(sequence: int) -> str:
    return f"replayed_tool_call_{sequence}"
