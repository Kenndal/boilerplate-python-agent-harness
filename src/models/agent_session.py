from uuid import UUID

from pydantic import ConfigDict

from src.models.agent import AgentMessage
from src.models.base import BaseAudit, BaseModelWithConfig


class AgentSessionCreate(BaseModelWithConfig):
    title: str | None = None


class AgentSessionUpdate(BaseModelWithConfig):
    title: str | None = None
    is_active: bool = True


class AgentSession(BaseModelWithConfig, BaseAudit):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_user_id: str
    title: str | None = None
    is_active: bool


class AgentSessionWithMessages(AgentSession):
    messages: list[AgentMessage] = []
