import uuid

from src.database.entities.agent_session import AgentSessionEntity
from src.models.agent_session import AgentSessionCreate


def to_agent_session_entity(model: AgentSessionCreate, user_id: str) -> AgentSessionEntity:
    return AgentSessionEntity(
        id=uuid.uuid4(),
        owner_user_id=user_id,
        title=model.title,
        is_active=True,
        created_by_user_id=user_id,
        last_modified_by_user_id=user_id,
    )
