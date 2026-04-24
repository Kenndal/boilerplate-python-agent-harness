import logging
from uuid import UUID

from result import Err, Ok, Result

from src.data_services.agent_message_data_service import AgentMessageDataService
from src.data_services.agent_session_data_service import AgentSessionDataService
from src.data_services.filters import EqualsFilter
from src.database.entities.agent_message import AgentMessageEntity
from src.database.entities.agent_session import AgentSessionEntity
from src.models.agent import AgentMessage
from src.models.agent_session import (
    AgentSession,
    AgentSessionCreate,
    AgentSessionUpdate,
    AgentSessionWithMessages,
)
from src.models.base import ModelList
from src.models.enums.error_status import ErrorStatus
from src.models.enums.sort_direction import SortDirection
from src.models.error_result import ErrorResult
from src.services.base_service import BaseService
from src.utils.exceptions import CrudError

logger = logging.getLogger(__name__)


class AgentSessionService(BaseService[AgentSessionEntity, AgentSession, AgentSessionCreate, AgentSessionUpdate]):
    data_service: AgentSessionDataService
    message_data_service: AgentMessageDataService
    model_class = AgentSession

    def __init__(
        self,
        data_service: AgentSessionDataService,
        message_data_service: AgentMessageDataService,
    ) -> None:
        super().__init__(data_service=data_service)
        self.message_data_service = message_data_service

    async def get_page(
        self,
        page_number: int,
        page_size: int,
        omit_pagination: bool,
        owner_user_id: str | None = None,
        is_active: bool | None = None,
        sort_by: str | None = None,
        sort_direction: SortDirection = SortDirection.ascending,
    ) -> Result[ModelList[AgentSession], ErrorResult]:
        filters = []
        if owner_user_id is not None:
            filters.append(EqualsFilter(field=AgentSessionEntity.owner_user_id, value=owner_user_id))
        if is_active is not None:
            filters.append(EqualsFilter(field=AgentSessionEntity.is_active, value=is_active))

        return await super().get_page(
            page_number=page_number,
            page_size=page_size,
            omit_pagination=omit_pagination,
            filters=filters,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )

    async def get_session_by_id_for_user(self, session_id: UUID, user_id: str) -> Result[AgentSession, ErrorResult]:
        """Return the session only when it belongs to the caller.

        Deliberately returns `NOT_FOUND` (not `FORBIDDEN`) on an owner mismatch so the API
        does not leak the existence of sessions that belong to other callers.
        """
        match await self.get_by_id(session_id):
            case Ok(session) if session.owner_user_id == user_id and session.is_active:
                return Ok(session)
            case Ok(_):
                return Err(self._session_not_found(session_id))
            case Err(error) if error.status == ErrorStatus.NOT_FOUND_ERROR:
                return Err(error)
            case Err(error):
                return Err(error)
            case _:
                return Err(self._session_not_found(session_id))

    async def get_session_with_messages_for_user(
        self, session_id: UUID, user_id: str
    ) -> Result[AgentSessionWithMessages, ErrorResult]:
        match await self.get_session_by_id_for_user(session_id, user_id):
            case Err(error):
                return Err(error)
            case Ok(session):
                try:
                    rows, _ = await self.message_data_service.get_by_page(
                        omit_pagination=True,
                        filters=[EqualsFilter(field=AgentMessageEntity.session_id, value=session_id)],
                        sort_by="sequence",
                        sort_direction=SortDirection.ascending,
                    )
                except CrudError as e:
                    return Err(self._error_response(status=ErrorStatus.INTERNAL_ERROR, details=str(e)))
                return Ok(
                    AgentSessionWithMessages(
                        **session.model_dump(),
                        messages=[AgentMessage.model_validate(row) for row in rows],
                    )
                )
            case _:
                return Err(self._session_not_found(session_id))

    def _session_not_found(self, session_id: UUID) -> ErrorResult:
        return self._not_found_error_response(
            self.GET_BY_ID_NOT_FOUND_MSG.format(model_class=self.model_class.__name__, id=str(session_id))
        )
