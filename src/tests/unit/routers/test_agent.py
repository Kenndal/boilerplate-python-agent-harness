from unittest.mock import AsyncMock
from uuid import UUID

from pytest_mock import MockerFixture
from result import Err, Ok
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
)
from starlette.testclient import TestClient

from src.constants import AGENT_SESSIONS_PREFIX, AGENTS_PREFIX, VERSION_PREFIX
from src.models.agent import AgentMessage, AgentTurnResponse
from src.models.agent_session import AgentSession, AgentSessionWithMessages
from src.models.base import ModelList
from src.models.enums.error_status import ErrorStatus
from src.models.error_result import ErrorResult
from src.services.agent_conversation_service import AgentConversationService
from src.services.agent_session_service import AgentSessionService
from src.tests.utils import is_expected_result_json

SESSIONS_URL = f"/{VERSION_PREFIX}/{AGENTS_PREFIX}/{AGENT_SESSIONS_PREFIX}"


def test_list_sessions_returns_page(
    client: TestClient,
    agent_session: AgentSession,
    mocker: MockerFixture,
) -> None:
    page = ModelList[AgentSession](items=[agent_session], total=1)
    mocker.patch.object(AgentSessionService, "get_page", new_callable=AsyncMock, return_value=Ok(page))

    response = client.get(f"{SESSIONS_URL}/")

    assert response.status_code == HTTP_200_OK
    assert is_expected_result_json(response.json(), page)


def test_create_session(
    client: TestClient,
    agent_session: AgentSession,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(AgentSessionService, "create", new_callable=AsyncMock, return_value=Ok(agent_session))

    response = client.post(f"{SESSIONS_URL}/")

    assert response.status_code == HTTP_201_CREATED
    assert is_expected_result_json(response.json(), agent_session)


def test_get_session_returns_with_messages(
    client: TestClient,
    agent_session_id: UUID,
    agent_session_with_messages: AgentSessionWithMessages,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        AgentSessionService,
        "get_session_with_messages_for_user",
        new_callable=AsyncMock,
        return_value=Ok(agent_session_with_messages),
    )

    response = client.get(f"{SESSIONS_URL}/{agent_session_id}")

    assert response.status_code == HTTP_200_OK
    assert is_expected_result_json(response.json(), agent_session_with_messages)


def test_get_session_returns_404_on_foreign_session(
    client: TestClient,
    agent_session_id: UUID,
    mocker: MockerFixture,
) -> None:
    not_found = ErrorResult(status=ErrorStatus.NOT_FOUND_ERROR, details="missing")
    mocker.patch.object(
        AgentSessionService,
        "get_session_with_messages_for_user",
        new_callable=AsyncMock,
        return_value=Err(not_found),
    )

    response = client.get(f"{SESSIONS_URL}/{agent_session_id}")

    assert response.status_code == HTTP_404_NOT_FOUND


def test_delete_session_returns_204(
    client: TestClient,
    agent_session_id: UUID,
    agent_session: AgentSession,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        AgentSessionService,
        "get_session_by_id_for_user",
        new_callable=AsyncMock,
        return_value=Ok(agent_session),
    )
    mocker.patch.object(AgentSessionService, "delete", new_callable=AsyncMock, return_value=Ok(None))

    response = client.delete(f"{SESSIONS_URL}/{agent_session_id}")

    assert response.status_code == HTTP_204_NO_CONTENT


def test_delete_session_returns_404_on_foreign_session(
    client: TestClient,
    agent_session_id: UUID,
    mocker: MockerFixture,
) -> None:
    not_found = ErrorResult(status=ErrorStatus.NOT_FOUND_ERROR, details="missing")
    mocker.patch.object(
        AgentSessionService,
        "get_session_by_id_for_user",
        new_callable=AsyncMock,
        return_value=Err(not_found),
    )

    response = client.delete(f"{SESSIONS_URL}/{agent_session_id}")

    assert response.status_code == HTTP_404_NOT_FOUND


def test_send_message_returns_turn_response(
    client: TestClient,
    agent_session_id: UUID,
    agent_message: AgentMessage,
    mocker: MockerFixture,
) -> None:
    turn = AgentTurnResponse(output="hi", new_messages=[agent_message])
    mocker.patch.object(
        AgentConversationService,
        "send_message",
        new_callable=AsyncMock,
        return_value=Ok(turn),
    )

    response = client.post(
        f"{SESSIONS_URL}/{agent_session_id}/messages",
        json={"prompt": "hello"},
    )

    assert response.status_code == HTTP_200_OK
    assert is_expected_result_json(response.json(), turn)


def test_send_message_returns_404_when_conversation_errors(
    client: TestClient,
    agent_session_id: UUID,
    mocker: MockerFixture,
) -> None:
    not_found = ErrorResult(status=ErrorStatus.NOT_FOUND_ERROR, details="missing")
    mocker.patch.object(
        AgentConversationService,
        "send_message",
        new_callable=AsyncMock,
        return_value=Err(not_found),
    )

    response = client.post(
        f"{SESSIONS_URL}/{agent_session_id}/messages",
        json={"prompt": "hello"},
    )

    assert response.status_code == HTTP_404_NOT_FOUND


def test_send_message_validation_error_on_empty_prompt(
    client: TestClient,
    agent_session_id: UUID,
) -> None:
    response = client.post(
        f"{SESSIONS_URL}/{agent_session_id}/messages",
        json={"prompt": ""},
    )

    assert response.status_code == 400 or response.status_code == 422
