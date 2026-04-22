import uuid

from src.database.entities.agent_message import AgentMessageEntity
from src.models.agent import AgentMessageCreate


def to_agent_message_entity(model: AgentMessageCreate, user_id: str) -> AgentMessageEntity:
    return AgentMessageEntity(
        id=uuid.uuid4(),
        session_id=model.session_id,
        sequence=model.sequence,
        role=model.role.value,
        content=model.content,
        tool_name=model.tool_name,
        tool_call_id=model.tool_call_id,
        tool_payload=model.tool_payload,
        input_tokens=model.input_tokens,
        output_tokens=model.output_tokens,
        is_active=True,
        created_by_user_id=user_id,
        last_modified_by_user_id=user_id,
    )
