from uuid import UUID, uuid4

import pytest

from src.database.entities.agent_message import AgentMessageEntity
from src.database.entities.agent_session import AgentSessionEntity
from src.models.agent import AgentMessage, AgentMessageCreate, AgentRole
from src.models.agent_session import AgentSession, AgentSessionCreate, AgentSessionWithMessages
from src.models.base import BaseAudit


@pytest.fixture(scope="module")
def agent_session_id() -> UUID:
    return uuid4()


@pytest.fixture
def agent_session_create() -> AgentSessionCreate:
    return AgentSessionCreate(title=None)


@pytest.fixture
def agent_session(agent_session_id: UUID, agent_session_create: AgentSessionCreate, audit: BaseAudit) -> AgentSession:
    return AgentSession(
        id=agent_session_id,
        owner_user_id="system",
        is_active=True,
        **agent_session_create.model_dump(),
        **audit.model_dump(),
    )


@pytest.fixture
def foreign_agent_session(agent_session_id: UUID, audit: BaseAudit) -> AgentSession:
    return AgentSession(
        id=agent_session_id,
        owner_user_id="someone-else",
        title=None,
        is_active=True,
        **audit.model_dump(),
    )


@pytest.fixture
def agent_session_entity(agent_session: AgentSession) -> AgentSessionEntity:
    return AgentSessionEntity(**agent_session.model_dump())


@pytest.fixture
def agent_message_create(agent_session_id: UUID) -> AgentMessageCreate:
    return AgentMessageCreate(
        session_id=agent_session_id,
        sequence=0,
        role=AgentRole.user,
        content="Hello there",
    )


@pytest.fixture
def agent_message(agent_session_id: UUID, agent_message_create: AgentMessageCreate, audit: BaseAudit) -> AgentMessage:
    return AgentMessage(
        id=uuid4(),
        is_active=True,
        **agent_message_create.model_dump(),
        **audit.model_dump(),
    )


@pytest.fixture
def agent_message_entity(agent_message: AgentMessage) -> AgentMessageEntity:
    return AgentMessageEntity(**agent_message.model_dump())


@pytest.fixture
def agent_session_with_messages(agent_session: AgentSession, agent_message: AgentMessage) -> AgentSessionWithMessages:
    return AgentSessionWithMessages(**agent_session.model_dump(), messages=[agent_message])
