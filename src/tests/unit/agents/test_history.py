from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

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

from src.agents.messages_history_helpers import model_messages_to_creates, rows_to_model_messages
from src.database.entities.agent_message import AgentMessageEntity
from src.models.agent import AgentRole


def _make_row(
    session_id: UUID,
    sequence: int,
    role: AgentRole,
    content: str,
    tool_name: str | None = None,
    tool_call_id: str | None = None,
    tool_payload: dict[str, Any] | None = None,
) -> AgentMessageEntity:
    now = datetime.now(tz=UTC)
    return AgentMessageEntity(
        id=uuid4(),
        session_id=session_id,
        sequence=sequence,
        role=role.value,
        content=content,
        tool_name=tool_name,
        tool_call_id=tool_call_id,
        tool_payload=tool_payload,
        input_tokens=None,
        output_tokens=None,
        is_active=True,
        created_date=now,
        last_modified_date=now,
        created_by_user_id="system",
        last_modified_by_user_id="system",
    )


def test_rows_to_model_messages_round_trips_tool_call_trace() -> None:
    session_id = uuid4()
    rows = [
        _make_row(session_id, 0, AgentRole.system, "sys prompt"),
        _make_row(session_id, 1, AgentRole.user, "hello"),
        _make_row(
            session_id,
            2,
            AgentRole.tool_call,
            "count_active_users({})",
            tool_name="count_active_users",
            tool_call_id="call_1",
            tool_payload={},
        ),
        _make_row(
            session_id,
            3,
            AgentRole.tool_return,
            "5",
            tool_name="count_active_users",
            tool_call_id="call_1",
            tool_payload={"value": 5},
        ),
        _make_row(session_id, 4, AgentRole.assistant, "there are 5 users"),
    ]

    messages = rows_to_model_messages(rows)

    assert len(messages) == 5
    assert isinstance(messages[0], ModelRequest)
    assert isinstance(messages[0].parts[0], SystemPromptPart)
    assert isinstance(messages[1], ModelRequest)
    assert isinstance(messages[1].parts[0], UserPromptPart)
    assert isinstance(messages[2], ModelResponse)
    assert isinstance(messages[2].parts[0], ToolCallPart)
    assert messages[2].parts[0].tool_name == "count_active_users"
    assert messages[2].parts[0].tool_call_id == "call_1"
    assert isinstance(messages[3], ModelRequest)
    assert isinstance(messages[3].parts[0], ToolReturnPart)
    assert messages[3].parts[0].tool_call_id == "call_1"
    assert isinstance(messages[4], ModelResponse)
    assert isinstance(messages[4].parts[0], TextPart)


def test_model_messages_to_creates_assigns_monotonic_sequences() -> None:
    session_id = uuid4()
    messages: list[ModelMessage] = [
        ModelRequest(parts=[UserPromptPart(content="hello")]),
        ModelResponse(
            parts=[
                ToolCallPart(tool_name="lookup", args={"q": "x"}),
                TextPart(content="the answer is 42"),
            ]
        ),
    ]

    creates = model_messages_to_creates(
        messages=messages,
        session_id=session_id,
        start_sequence=5,
        input_tokens=100,
        output_tokens=50,
    )

    assert [c.sequence for c in creates] == [5, 6, 7]
    assert creates[0].role == AgentRole.user
    assert creates[1].role == AgentRole.tool_call
    assert creates[1].tool_payload == {"q": "x"}
    assert creates[1].tool_call_id is not None
    assert creates[2].role == AgentRole.assistant
    assert creates[2].input_tokens == 100
    assert creates[2].output_tokens == 50


def test_model_messages_to_creates_omits_tokens_when_no_assistant_row() -> None:
    session_id = uuid4()
    messages = [ModelRequest(parts=[UserPromptPart(content="hi")])]

    creates = model_messages_to_creates(
        messages=messages,
        session_id=session_id,
        start_sequence=0,
        input_tokens=10,
        output_tokens=1,
    )

    assert len(creates) == 1
    assert creates[0].role == AgentRole.user
    assert creates[0].input_tokens is None
    assert creates[0].output_tokens is None


def test_rows_to_model_messages_backfills_missing_tool_call_id() -> None:
    session_id = uuid4()
    rows = [
        _make_row(
            session_id,
            0,
            AgentRole.tool_call,
            'lookup({"q": "x"})',
            tool_name="lookup",
            tool_payload={"q": "x"},
        ),
        _make_row(
            session_id,
            1,
            AgentRole.tool_return,
            '{"value": 42}',
            tool_name="lookup",
            tool_payload={"value": 42},
        ),
    ]

    messages = rows_to_model_messages(rows)

    assert isinstance(messages[0], ModelResponse)
    assert isinstance(messages[1], ModelRequest)
    call_part = messages[0].parts[0]
    return_part = messages[1].parts[0]
    assert isinstance(call_part, ToolCallPart)
    assert isinstance(return_part, ToolReturnPart)
    assert call_part.tool_call_id == return_part.tool_call_id
