from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.entities.base import Base, BaseAuditEntity

if TYPE_CHECKING:
    from src.database.entities.agent_message import AgentMessageEntity


class AgentSessionEntity(Base, BaseAuditEntity):
    __tablename__ = "agent_session"

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True)
    owner_user_id: Mapped[str] = mapped_column(index=True)
    title: Mapped[str | None] = mapped_column(default=None)

    messages: Mapped[list["AgentMessageEntity"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="AgentMessageEntity.sequence",
    )
