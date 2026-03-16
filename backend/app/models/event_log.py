"""Event log — audit trail for all system events."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class EventLog(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "event_log"

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    entity_type: Mapped[str | None] = mapped_column(String(100))
    entity_id: Mapped["UUID | None"] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped["UUID | None"] = mapped_column(UUID(as_uuid=True))
    description: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    def __repr__(self) -> str:
        return f"<EventLog {self.event_type} at {self.timestamp}>"
