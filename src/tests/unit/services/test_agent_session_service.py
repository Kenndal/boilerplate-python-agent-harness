from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from pytest_mock import MockerFixture
from result import Err, Ok

from src.data_services.agent_message_data_service import AgentMessageDataService
from src.data_services.agent_session_data_service import AgentSessionDataService
from src.database.entities.agent_message import AgentMessageEntity
from src.database.entities.agent_session import AgentSessionEntity
from src.models.agent import AgentMessage
from src.models.agent_session import AgentSession, AgentSessionWithMessages
from src.models.base import ModelList
from src.models.enums.error_status import ErrorStatus
from src.models.error_result import ErrorResult
from src.services.agent_session_service import AgentSessionService


async def test_get_page_filters_on_owner(
    agent_session_service: AgentSessionService,
    agent_session_entity: AgentSessionEntity,
    agent_session: AgentSession,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        AgentSessionDataService,
        "get_by_page",
        new_callable=AsyncMock,
        return_value=([agent_session_entity], 1),
    )

    result = await agent_session_service.get_page(
        page_number=1,
        page_size=10,
        omit_pagination=False,
        owner_user_id=agent_session.owner_user_id,
    )

    assert result == Ok(ModelList[AgentSession](items=[agent_session], total=1))


async def test_get_by_id_for_user_returns_session_when_owner_matches(
    agent_session_service: AgentSessionService,
    agent_session: AgentSession,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        AgentSessionService,
        "get_by_id",
        new_callable=AsyncMock,
        return_value=Ok(agent_session),
    )

    result = await agent_session_service.get_session_by_id_for_user(agent_session.id, agent_session.owner_user_id)

    assert result == Ok(agent_session)


async def test_get_by_id_for_user_returns_not_found_on_owner_mismatch(
    agent_session_service: AgentSessionService,
    foreign_agent_session: AgentSession,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        AgentSessionService,
        "get_by_id",
        new_callable=AsyncMock,
        return_value=Ok(foreign_agent_session),
    )

    result = await agent_session_service.get_session_by_id_for_user(foreign_agent_session.id, "some-other-user")

    assert isinstance(result, Err)
    assert result.err_value.status == ErrorStatus.NOT_FOUND_ERROR


async def test_get_by_id_for_user_returns_not_found_when_inactive(
    agent_session_service: AgentSessionService,
    agent_session: AgentSession,
    mocker: MockerFixture,
) -> None:
    inactive = agent_session.model_copy(update={"is_active": False})
    mocker.patch.object(
        AgentSessionService,
        "get_by_id",
        new_callable=AsyncMock,
        return_value=Ok(inactive),
    )

    result = await agent_session_service.get_session_by_id_for_user(inactive.id, inactive.owner_user_id)

    assert isinstance(result, Err)
    assert result.err_value.status == ErrorStatus.NOT_FOUND_ERROR


async def test_get_by_id_for_user_propagates_not_found_error(
    agent_session_service: AgentSessionService,
    mocker: MockerFixture,
) -> None:
    not_found = ErrorResult(status=ErrorStatus.NOT_FOUND_ERROR, details="missing")
    mocker.patch.object(
        AgentSessionService,
        "get_by_id",
        new_callable=AsyncMock,
        return_value=Err(not_found),
    )

    result = await agent_session_service.get_session_by_id_for_user(uuid4(), "system")

    assert result == Err(not_found)


async def test_get_with_messages_for_user(
    agent_session_service: AgentSessionService,
    agent_session: AgentSession,
    agent_message: AgentMessage,
    agent_message_entity: AgentMessageEntity,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        AgentSessionService,
        "get_session_by_id_for_user",
        new_callable=AsyncMock,
        return_value=Ok(agent_session),
    )
    mocker.patch.object(
        AgentMessageDataService,
        "get_by_page",
        new_callable=AsyncMock,
        return_value=([agent_message_entity], 1),
    )

    result = await agent_session_service.get_session_with_messages_for_user(
        agent_session.id, agent_session.owner_user_id
    )

    assert isinstance(result, Ok)
    returned = result.ok_value
    assert isinstance(returned, AgentSessionWithMessages)
    assert returned.id == agent_session.id
    assert len(returned.messages) == 1
    assert returned.messages[0].id == agent_message.id


async def test_get_with_messages_for_user_propagates_session_error(
    agent_session_service: AgentSessionService,
    mocker: MockerFixture,
) -> None:
    err = ErrorResult(status=ErrorStatus.NOT_FOUND_ERROR, details="missing")
    mocker.patch.object(
        AgentSessionService,
        "get_session_by_id_for_user",
        new_callable=AsyncMock,
        return_value=Err(err),
    )

    result = await agent_session_service.get_session_with_messages_for_user(uuid4(), "system")

    assert result == Err(err)


def _as_uuid(value: str) -> UUID:
    return UUID(value)
