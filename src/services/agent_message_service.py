import logging
from uuid import UUID

from result import Err, Ok, Result

from src.data_services.agent_message_data_service import AgentMessageDataService
from src.data_services.filters import EqualsFilter
from src.database.entities.agent_message import AgentMessageEntity
from src.mappers.agent_message import to_agent_message_entity
from src.models.agent import AgentMessage, AgentMessageCreate, AgentMessageUpdate
from src.models.enums.error_status import ErrorStatus
from src.models.enums.sort_direction import SortDirection
from src.models.error_result import ErrorResult
from src.services.base_service import BaseService
from src.utils.exceptions import CrudError

logger = logging.getLogger(__name__)


class AgentMessageService(BaseService[AgentMessageEntity, AgentMessage, AgentMessageCreate, AgentMessageUpdate]):
    data_service: AgentMessageDataService
    model_class = AgentMessage

    async def list_for_session(self, session_id: UUID) -> Result[list[AgentMessage], ErrorResult]:
        try:
            rows, _ = await self.data_service.get_by_page(
                omit_pagination=True,
                filters=[EqualsFilter(field=AgentMessageEntity.session_id, value=session_id)],
                sort_by="sequence",
                sort_direction=SortDirection.ascending,
            )
        except CrudError as e:
            return Err(self._error_response(status=ErrorStatus.INTERNAL_ERROR, details=str(e)))
        return Ok([AgentMessage.model_validate(row) for row in rows])

    async def max_sequence(self, session_id: UUID) -> Result[int, ErrorResult]:
        try:
            return Ok(await self.data_service.max_sequence(session_id))
        except CrudError as e:
            return Err(self._error_response(status=ErrorStatus.INTERNAL_ERROR, details=str(e)))

    async def append_many(
        self, creates: list[AgentMessageCreate], user_id: str
    ) -> Result[list[AgentMessage], ErrorResult]:
        """Persist a batch of turn rows produced by a single agent run.

        Each row is created independently so a failure on the Nth row leaves the first N-1
        persisted; the surrounding `get_db()` transaction rolls them all back together.
        """
        persisted: list[AgentMessage] = []
        for create in creates:
            match await self.create(
                model=create,
                mapper=to_agent_message_entity,  # ty: ignore[invalid-argument-type]
                user_id=user_id,
            ):
                case Ok(message):
                    persisted.append(message)
                case Err(error):
                    return Err(error)
                case _:
                    return Err(
                        self._error_response(
                            status=ErrorStatus.INTERNAL_ERROR,
                            details="Failed to persist agent message rows",
                        )
                    )
        return Ok(persisted)
