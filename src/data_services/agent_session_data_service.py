from sqlalchemy.ext.asyncio import AsyncSession

from src.data_services.crud import Crud
from src.database.entities.agent_session import AgentSessionEntity
from src.models.agent_session import AgentSessionCreate, AgentSessionUpdate


class AgentSessionDataService(Crud[AgentSessionEntity, AgentSessionCreate, AgentSessionUpdate]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(
            session=session,
            entity_type=AgentSessionEntity,
        )
