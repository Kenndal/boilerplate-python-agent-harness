import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_services.crud import Crud
from src.database.entities.agent_message import AgentMessageEntity
from src.models.agent import AgentMessageCreate, AgentMessageUpdate
from src.utils.exceptions import CrudError

logger = logging.getLogger(__name__)


class AgentMessageDataService(Crud[AgentMessageEntity, AgentMessageCreate, AgentMessageUpdate]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(
            session=session,
            entity_type=AgentMessageEntity,
        )

    async def max_sequence(self, session_id: UUID) -> int:
        """Return the largest `sequence` for a session, or -1 when the session has no messages.

        Callers derive the next sequence as `max_sequence + 1`; returning -1 for empty keeps
        the arithmetic correct without a separate branch at the call site.
        """
        try:
            stmt = (
                select(AgentMessageEntity.sequence)
                .where(AgentMessageEntity.session_id == session_id)
                .order_by(AgentMessageEntity.sequence.desc())
                .limit(1)
            )
            result = await self.session.scalar(stmt)
            return int(result) if result is not None else -1
        except Exception as e:
            error_msg = f"Failed to read max sequence for session {session_id}"
            logger.error(f"{error_msg}, {str(e)}")
            raise CrudError(error_msg) from e
