from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.config import config
from src.database.entities.base import Base, BaseAuditEntity

if TYPE_CHECKING:
    from src.database.entities.agent_session import AgentSessionEntity


class AgentMessageEntity(Base, BaseAuditEntity):
    __tablename__ = "agent_message"
    __table_args__ = (UniqueConstraint("session_id", "sequence", name="uq_agent_message_session_sequence"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{config.DATABASE_SCHEMA}.agent_session.id", ondelete="CASCADE"), index=True
    )
    sequence: Mapped[int]
    role: Mapped[str]
    content: Mapped[str]
    tool_name: Mapped[str | None] = mapped_column(default=None)
    tool_call_id: Mapped[str | None] = mapped_column(default=None)
    tool_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    input_tokens: Mapped[int | None] = mapped_column(default=None)
    output_tokens: Mapped[int | None] = mapped_column(default=None)

    session: Mapped["AgentSessionEntity"] = relationship(back_populates="messages")
