from unittest.mock import AsyncMock

from pytest_mock import MockerFixture
from result import Err, Ok

from src.data_services.agent_message_data_service import AgentMessageDataService
from src.database.entities.agent_message import AgentMessageEntity
from src.models.agent import AgentMessage, AgentMessageCreate, AgentRole
from src.models.enums.error_status import ErrorStatus
from src.services.agent_message_service import AgentMessageService
from src.utils.exceptions import CrudError


async def test_list_for_session_returns_rows(
    agent_message_service: AgentMessageService,
    agent_message_entity: AgentMessageEntity,
    agent_message: AgentMessage,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        AgentMessageDataService,
        "get_by_page",
        new_callable=AsyncMock,
        return_value=([agent_message_entity], 1),
    )

    result = await agent_message_service.list_for_session(agent_message.session_id)

    assert isinstance(result, Ok)
    assert len(result.ok_value) == 1
    assert result.ok_value[0].id == agent_message.id


async def test_list_for_session_returns_internal_error_on_crud_failure(
    agent_message_service: AgentMessageService,
    agent_message: AgentMessage,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        AgentMessageDataService,
        "get_by_page",
        new_callable=AsyncMock,
        side_effect=CrudError("boom"),
    )

    result = await agent_message_service.list_for_session(agent_message.session_id)

    assert isinstance(result, Err)
    assert result.err_value.status == ErrorStatus.INTERNAL_ERROR


async def test_max_sequence_delegates_to_data_service(
    agent_message_service: AgentMessageService,
    agent_message: AgentMessage,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        AgentMessageDataService,
        "max_sequence",
        new_callable=AsyncMock,
        return_value=7,
    )

    result = await agent_message_service.max_sequence(agent_message.session_id)

    assert result == Ok(7)


async def test_append_many_persists_all_rows(
    agent_message_service: AgentMessageService,
    agent_message: AgentMessage,
    mocker: MockerFixture,
) -> None:
    create = AgentMessageCreate(
        session_id=agent_message.session_id,
        sequence=0,
        role=AgentRole.user,
        content="Hi",
    )
    mocker.patch.object(
        AgentMessageService,
        "create",
        new_callable=AsyncMock,
        return_value=Ok(agent_message),
    )

    result = await agent_message_service.append_many([create, create], user_id="system")

    assert isinstance(result, Ok)
    assert len(result.ok_value) == 2
    assert result.ok_value[0].id == agent_message.id
