from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
import pytest
from pytest_mock import MockerFixture
from result import Err, Ok

from src.agents.deps import AgentDeps
from src.agents.runner import AgentRunner, RunnerOutput
from src.models.agent import AgentMessage, AgentMessageCreate, AgentRole, AgentTurnResponse
from src.models.agent_session import AgentSession
from src.models.enums.error_status import ErrorStatus
from src.models.error_result import ErrorResult
from src.services.agent_conversation_service import AgentConversationService
from src.services.agent_message_service import AgentMessageService
from src.services.agent_session_service import AgentSessionService


@pytest.fixture
def runner() -> AgentRunner:
    return AgentRunner()


@pytest.fixture
def conversation_service(
    agent_session_service: AgentSessionService,
    agent_message_service: AgentMessageService,
    runner: AgentRunner,
) -> AgentConversationService:
    return AgentConversationService(
        session_service=agent_session_service,
        message_service=agent_message_service,
        runner=runner,
        max_history_messages=3,
    )


@pytest.fixture
def agent_deps() -> AgentDeps:
    return AgentDeps(user_id="system", user_service=MagicMock())


async def test_send_message_returns_not_found_when_session_missing(
    conversation_service: AgentConversationService,
    agent_deps: AgentDeps,
    mocker: MockerFixture,
) -> None:
    err = ErrorResult(status=ErrorStatus.NOT_FOUND_ERROR, details="missing")
    mocker.patch.object(AgentSessionService, "get_session_by_id_for_user", new_callable=AsyncMock, return_value=Err(err))

    result = await conversation_service.send_message(
        session_id=uuid4(),
        prompt="hi",
        user_id="system",
        agent_deps=agent_deps,
    )

    assert result == Err(err)


async def test_send_message_persists_new_turn_rows(
    conversation_service: AgentConversationService,
    agent_session: AgentSession,
    agent_message: AgentMessage,
    agent_deps: AgentDeps,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        AgentSessionService,
        "get_session_by_id_for_user",
        new_callable=AsyncMock,
        return_value=Ok(agent_session),
    )
    mocker.patch.object(
        AgentMessageService,
        "list_for_session",
        new_callable=AsyncMock,
        return_value=Ok([]),
    )

    new_messages: list[ModelMessage] = [
        ModelRequest(parts=[UserPromptPart(content="hello")]),
        ModelResponse(parts=[TextPart(content="hi back")]),
    ]
    mocker.patch.object(
        AgentRunner,
        "run",
        new_callable=AsyncMock,
        return_value=Ok(
            RunnerOutput(
                output="hi back",
                new_messages=new_messages,
                input_tokens=10,
                output_tokens=3,
            )
        ),
    )
    mocker.patch.object(AgentMessageService, "max_sequence", new_callable=AsyncMock, return_value=Ok(-1))

    append_many_mock = mocker.patch.object(
        AgentMessageService,
        "append_many",
        new_callable=AsyncMock,
        return_value=Ok([agent_message, agent_message]),
    )

    result = await conversation_service.send_message(
        session_id=agent_session.id,
        prompt="hello",
        user_id=agent_session.owner_user_id,
        agent_deps=agent_deps,
    )

    assert isinstance(result, Ok)
    turn = result.ok_value
    assert isinstance(turn, AgentTurnResponse)
    assert turn.output == "hi back"
    assert len(turn.new_messages) == 2

    creates: list[AgentMessageCreate] = append_many_mock.call_args.kwargs["creates"]
    assert [c.sequence for c in creates] == [0, 1]
    assert creates[0].role == AgentRole.user
    assert creates[1].role == AgentRole.assistant
    assert creates[1].input_tokens == 10
    assert creates[1].output_tokens == 3


async def test_send_message_returns_internal_error_when_history_lookup_fails(
    conversation_service: AgentConversationService,
    agent_session: AgentSession,
    agent_deps: AgentDeps,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        AgentSessionService,
        "get_session_by_id_for_user",
        new_callable=AsyncMock,
        return_value=Ok(agent_session),
    )
    mocker.patch.object(
        AgentMessageService,
        "list_for_session",
        new_callable=AsyncMock,
        return_value=Err(ErrorResult(status=ErrorStatus.INTERNAL_ERROR, details="db down")),
    )

    result = await conversation_service.send_message(
        session_id=agent_session.id,
        prompt="hello",
        user_id=agent_session.owner_user_id,
        agent_deps=agent_deps,
    )

    assert isinstance(result, Err)
    assert result.err_value.status == ErrorStatus.INTERNAL_ERROR


async def test_send_message_clips_history_to_max_size(
    conversation_service: AgentConversationService,
    agent_session: AgentSession,
    agent_message: AgentMessage,
    agent_deps: AgentDeps,
    mocker: MockerFixture,
) -> None:
    older_rows = [
        agent_message.model_copy(update={"id": uuid4(), "sequence": i, "role": AgentRole.user, "content": f"turn {i}"})
        for i in range(10)
    ]
    mocker.patch.object(
        AgentSessionService, "get_session_by_id_for_user", new_callable=AsyncMock, return_value=Ok(agent_session)
    )
    mocker.patch.object(
        AgentMessageService,
        "list_for_session",
        new_callable=AsyncMock,
        return_value=Ok(older_rows),
    )

    runner_run = mocker.patch.object(
        AgentRunner,
        "run",
        new_callable=AsyncMock,
        return_value=Ok(
            RunnerOutput(
                output="ok",
                new_messages=[ModelRequest(parts=[UserPromptPart(content="next")])],
                input_tokens=None,
                output_tokens=None,
            )
        ),
    )
    mocker.patch.object(AgentMessageService, "max_sequence", new_callable=AsyncMock, return_value=Ok(9))
    mocker.patch.object(
        AgentMessageService,
        "append_many",
        new_callable=AsyncMock,
        return_value=Ok([agent_message]),
    )

    result = await conversation_service.send_message(
        session_id=agent_session.id,
        prompt="next",
        user_id=agent_session.owner_user_id,
        agent_deps=agent_deps,
    )

    assert isinstance(result, Ok)
    history_arg = runner_run.call_args.kwargs["history"]
    assert history_arg is not None
    assert len(history_arg) == 3
    first_part = history_arg[0].parts[0]
    assert isinstance(first_part, UserPromptPart)
    assert first_part.content == "turn 7"


async def test_send_message_propagates_runner_error(
    conversation_service: AgentConversationService,
    agent_session: AgentSession,
    agent_deps: AgentDeps,
    mocker: MockerFixture,
) -> None:
    runner_err = ErrorResult(status=ErrorStatus.INTERNAL_ERROR, details="model down")
    mocker.patch.object(
        AgentSessionService, "get_session_by_id_for_user", new_callable=AsyncMock, return_value=Ok(agent_session)
    )
    mocker.patch.object(AgentMessageService, "list_for_session", new_callable=AsyncMock, return_value=Ok([]))
    mocker.patch.object(AgentRunner, "run", new_callable=AsyncMock, return_value=Err(runner_err))

    result = await conversation_service.send_message(
        session_id=agent_session.id,
        prompt="hello",
        user_id=agent_session.owner_user_id,
        agent_deps=agent_deps,
    )

    assert result == Err(runner_err)


def _ensure_uuid(value: str) -> UUID:
    return UUID(value)
