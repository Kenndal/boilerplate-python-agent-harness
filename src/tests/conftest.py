from collections.abc import Iterator
from datetime import UTC, datetime
from typing import cast
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import TestClient

from src.api_server.deps import get_default_agent
from src.api_server.main import app
from src.data_services.agent_message_data_service import AgentMessageDataService
from src.data_services.agent_session_data_service import AgentSessionDataService
from src.data_services.user_data_service import UserDataService
from src.models.base import BaseAudit
from src.models.enums.error_status import ErrorStatus
from src.models.error_result import ErrorResult
from src.services.agent_message_service import AgentMessageService
from src.services.agent_session_service import AgentSessionService
from src.services.user_service import UserService

pytest_plugins = [
    "src.tests.fixtures.agent_fixtures",
    "src.tests.fixtures.user_fixtures",
]


@pytest.fixture(scope="session")
def user_id() -> str:
    return str(uuid4())


@pytest.fixture(scope="session")
def fake_user_id() -> str:
    return "fake_user_id"


@pytest.fixture
def client() -> Iterator[TestClient]:
    mock_agent = AsyncMock()
    app.dependency_overrides[get_default_agent] = lambda: mock_agent
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_default_agent, None)


@pytest.fixture(scope="session")
def audit(user_id: str) -> BaseAudit:
    now = datetime.now(tz=UTC)
    return BaseAudit(
        created_date=now,
        last_modified_date=now,
        created_by_user_id=user_id,
        last_modified_by_user_id=user_id,
    )


@pytest.fixture
def session() -> AsyncSession:
    return cast(AsyncSession, AsyncMock(spec=AsyncSession))


@pytest.fixture
def user_data_service(session: AsyncSession) -> UserDataService:
    return UserDataService(session=session)


@pytest.fixture
def user_service(user_data_service: UserDataService) -> UserService:
    return UserService(data_service=user_data_service)


@pytest.fixture
def error_result_internal_error() -> ErrorResult:
    return ErrorResult(status=ErrorStatus.INTERNAL_ERROR, details="error")


@pytest.fixture
def agent_session_data_service(session: AsyncSession) -> AgentSessionDataService:
    return AgentSessionDataService(session=session)


@pytest.fixture
def agent_message_data_service(session: AsyncSession) -> AgentMessageDataService:
    return AgentMessageDataService(session=session)


@pytest.fixture
def agent_session_service(
    agent_session_data_service: AgentSessionDataService,
    agent_message_data_service: AgentMessageDataService,
) -> AgentSessionService:
    return AgentSessionService(
        data_service=agent_session_data_service,
        message_data_service=agent_message_data_service,
    )


@pytest.fixture
def agent_message_service(
    agent_message_data_service: AgentMessageDataService,
) -> AgentMessageService:
    return AgentMessageService(data_service=agent_message_data_service)
