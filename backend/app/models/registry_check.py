"""Registry check results — open registries of Ukraine."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RegistryType(StrEnum):
    EDR = "edr"                  # ЄДР (юрособи / ФОП)
    DRORM = "drorm"              # Реєстр нерухомості
    ASVP = "asvp"                # Реєстр виконавчих проваджень
    COURT_REGISTRY = "court"     # ЄДРСР — судовий реєстр
    BANKRUPTCY = "bankruptcy"    # Реєстр банкрутства
    WANTED = "wanted"            # Реєстр розшуку
    SANCTIONS = "sanctions"      # Санкційні списки
    DEBTORS = "debtors"          # Єдиний реєстр боржників


class RegistryCheck(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "registry_checks"

    debtor_id: Mapped["UUID"] = mapped_column(
        UUID(as_uuid=True), ForeignKey("debtors.id"), nullable=False
    )
    registry_type: Mapped[RegistryType] = mapped_column(
        Enum(RegistryType, name="registry_type_enum"), nullable=False
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    raw_response: Mapped[dict | None] = mapped_column(JSONB)
    summary: Mapped[str | None] = mapped_column(Text)
    has_records: Mapped[bool] = mapped_column(default=False)
    error_message: Mapped[str | None] = mapped_column(String(500))

    debtor: Mapped["Debtor"] = relationship(back_populates="registry_checks")  # noqa: F821

    def __repr__(self) -> str:
        return f"<RegistryCheck {self.registry_type} debtor={self.debtor_id}>"
