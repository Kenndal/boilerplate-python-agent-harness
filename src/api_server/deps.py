from collections.abc import AsyncGenerator
from typing import cast

from fastapi import Depends
from pydantic_ai import Agent
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from src.agents.deps import AgentDeps
from src.agents.runner import AgentRunner
from src.data_services.agent_message_data_service import AgentMessageDataService
from src.data_services.agent_session_data_service import AgentSessionDataService
from src.data_services.user_data_service import UserDataService
from src.database.db_engine import AsyncSessionMaker
from src.services.agent_conversation_service import AgentConversationService
from src.services.agent_message_service import AgentMessageService
from src.services.agent_session_service import AgentSessionService
from src.services.user_service import UserService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionMaker() as session, session.begin():
        yield session


def get_user_data_service(db_session: AsyncSession = Depends(get_db)) -> UserDataService:
    return UserDataService(session=db_session)


def get_user_service(user_data_service: UserDataService = Depends(get_user_data_service)) -> UserService:
    return UserService(data_service=user_data_service)


def get_current_user_id() -> str:
    # Placeholder for actual authentication integration.  Real implementations should resolve
    # the caller's identity from a JWT / session / etc. and return a stable user id.
    return "system"


def get_agent_deps(
    current_user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends(get_user_service),
) -> AgentDeps:
    return AgentDeps(user_id=current_user_id, user_service=user_service)


def get_agent_session_data_service(
    db_session: AsyncSession = Depends(get_db),
) -> AgentSessionDataService:
    return AgentSessionDataService(session=db_session)


def get_agent_message_data_service(
    db_session: AsyncSession = Depends(get_db),
) -> AgentMessageDataService:
    return AgentMessageDataService(session=db_session)


def get_agent_session_service(
    session_data_service: AgentSessionDataService = Depends(get_agent_session_data_service),
    message_data_service: AgentMessageDataService = Depends(get_agent_message_data_service),
) -> AgentSessionService:
    return AgentSessionService(
        data_service=session_data_service,
        message_data_service=message_data_service,
    )


def get_agent_message_service(
    message_data_service: AgentMessageDataService = Depends(get_agent_message_data_service),
) -> AgentMessageService:
    return AgentMessageService(data_service=message_data_service)


def get_default_agent(request: Request) -> Agent[AgentDeps, str]:
    return cast(Agent[AgentDeps, str], request.app.state.default_agent)


def get_default_agent_runner(agent: Agent[AgentDeps, str] = Depends(get_default_agent)) -> AgentRunner:
    return AgentRunner(agent=agent)


def get_agent_conversation_service(
    session_service: AgentSessionService = Depends(get_agent_session_service),
    message_service: AgentMessageService = Depends(get_agent_message_service),
    runner: AgentRunner = Depends(get_default_agent_runner),
) -> AgentConversationService:
    return AgentConversationService(
        session_service=session_service,
        message_service=message_service,
        runner=runner,
    )
