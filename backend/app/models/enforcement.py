"""Enforcement proceeding and party substitution models."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EnforcementProceeding(Base):
    """An enforcement proceeding (виконавче провадження)."""

    __tablename__ = "enforcement_proceedings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    debtor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("debtors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    court_case_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("court_cases.id", ondelete="SET NULL"), index=True
    )

    proceeding_number: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    executor_name: Mapped[str | None] = mapped_column(String(255))
    executor_office: Mapped[str | None] = mapped_column(String(255))

    status: Mapped[str] = mapped_column(
        String(30), default="active", index=True
    )  # active / completed / suspended / returned
    opened_date: Mapped[date | None] = mapped_column(Date)
    closed_date: Mapped[date | None] = mapped_column(Date)

    enforcement_document_type: Mapped[str | None] = mapped_column(String(50))
    enforcement_document_number: Mapped[str | None] = mapped_column(String(100))

    total_debt: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    collected_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), default=0)

    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    debtor: Mapped["Debtor"] = relationship(back_populates="enforcement_proceedings")
    party_substitutions: Mapped[list["PartySubstitution"]] = relationship(
        back_populates="enforcement_proceeding"
    )


class PartySubstitution(Base):
    """Party substitution in enforcement (заміна сторони)."""

    __tablename__ = "party_substitutions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    enforcement_proceeding_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("enforcement_proceedings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    substitution_date: Mapped[date | None] = mapped_column(Date)
    old_party_name: Mapped[str] = mapped_column(String(255), nullable=False)
    new_party_name: Mapped[str] = mapped_column(String(255), nullable=False)
    court_ruling_number: Mapped[str | None] = mapped_column(String(50))
    basis_document: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending / completed

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    enforcement_proceeding: Mapped["EnforcementProceeding"] = relationship(
        back_populates="party_substitutions"
    )
