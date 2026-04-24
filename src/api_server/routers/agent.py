from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query
from result import Err, Ok
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from src.agents.deps import AgentDeps
from src.api_server.deps import (
    get_agent_conversation_service,
    get_agent_deps,
    get_agent_session_service,
    get_current_user_id,
)
from src.api_server.helpers.error_response import http_exception_from_error
from src.api_server.responses import response_404
from src.constants import (
    AGENT_SESSIONS_PREFIX,
    AGENTS_PREFIX,
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    OMIT_PAGINATION,
    PAGE_NUMBER,
    PAGE_SIZE,
    SORT_BY,
    SORT_DIRECTION,
)
from src.mappers.agent_session import to_agent_session_entity
from src.models.agent import AgentPromptRequest, AgentTurnResponse
from src.models.agent_session import (
    AgentSession,
    AgentSessionCreate,
    AgentSessionWithMessages,
)
from src.models.base import ModelList
from src.models.enums.sort_direction import SortDirection
from src.services.agent_conversation_service import AgentConversationService
from src.services.agent_session_service import AgentSessionService

router = APIRouter(prefix=f"/{AGENTS_PREFIX}/{AGENT_SESSIONS_PREFIX}")


@router.get("/", response_model=ModelList[AgentSession])
async def list_sessions(
    page_number: int = Query(default=DEFAULT_PAGE_NUMBER, alias=PAGE_NUMBER, gt=0),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, alias=PAGE_SIZE, gt=0),
    omit_pagination: bool = Query(default=False, alias=OMIT_PAGINATION),
    is_active: bool | None = Query(default=None),
    sort_by: str | None = Query(default=None, alias=SORT_BY),
    sort_direction: SortDirection = Query(default=SortDirection.ascending, alias=SORT_DIRECTION),
    current_user_id: str = Depends(get_current_user_id),
    session_service: AgentSessionService = Depends(get_agent_session_service),
) -> ModelList[AgentSession]:
    match await session_service.get_page(
        page_number=page_number,
        page_size=page_size,
        omit_pagination=omit_pagination,
        owner_user_id=current_user_id,
        is_active=is_active,
        sort_by=sort_by,
        sort_direction=sort_direction,
    ):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.post("/", response_model=AgentSession, status_code=HTTP_201_CREATED)
async def create_session(
    current_user_id: str = Depends(get_current_user_id),
    session_service: AgentSessionService = Depends(get_agent_session_service),
) -> AgentSession:
    create_model = AgentSessionCreate()
    match await session_service.create(
        create_model,
        to_agent_session_entity,  # ty: ignore[invalid-argument-type]
        current_user_id,
    ):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.get("/{session_id}", response_model=AgentSessionWithMessages, responses=response_404)
async def get_session(
    session_id: UUID = Path(...),
    current_user_id: str = Depends(get_current_user_id),
    session_service: AgentSessionService = Depends(get_agent_session_service),
) -> AgentSessionWithMessages:
    match await session_service.get_session_with_messages_for_user(session_id, current_user_id):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()


@router.delete("/{session_id}", status_code=HTTP_204_NO_CONTENT, responses=response_404)
async def delete_session(
    session_id: UUID = Path(...),
    current_user_id: str = Depends(get_current_user_id),
    session_service: AgentSessionService = Depends(get_agent_session_service),
) -> None:
    match await session_service.get_session_by_id_for_user(session_id, current_user_id):
        case Err(error):
            raise http_exception_from_error(error)
        case Ok(_):
            pass
        case _:
            raise http_exception_from_error()

    match await session_service.delete(session_id):
        case Err(error):
            raise http_exception_from_error(error)


@router.post("/{session_id}/messages", response_model=AgentTurnResponse, responses=response_404)
async def send_message(
    payload: AgentPromptRequest,
    session_id: UUID = Path(...),
    current_user_id: str = Depends(get_current_user_id),
    agent_deps: AgentDeps = Depends(get_agent_deps),
    conversation_service: AgentConversationService = Depends(get_agent_conversation_service),
) -> AgentTurnResponse:
    match await conversation_service.send_message(
        session_id=session_id,
        prompt=payload.prompt,
        user_id=current_user_id,
        agent_deps=agent_deps,
    ):
        case Ok(result):
            return result
        case Err(error):
            raise http_exception_from_error(error)
        case _:
            raise http_exception_from_error()
