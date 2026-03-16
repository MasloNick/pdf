"""Debtor models."""

from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Debtor(Base):
    """Individual or legal entity debtor."""

    __tablename__ = "debtors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # -- Identification --
    debtor_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="individual"
    )  # individual / legal_entity
    last_name: Mapped[str | None] = mapped_column(String(100), index=True)
    first_name: Mapped[str | None] = mapped_column(String(100))
    patronymic: Mapped[str | None] = mapped_column(String(100))
    full_name: Mapped[str | None] = mapped_column(String(300), index=True)  # for legal entities
    ipn: Mapped[str | None] = mapped_column(String(10), unique=True, index=True)  # IPN / tax ID
    edrpou: Mapped[str | None] = mapped_column(String(8), unique=True, index=True)  # EDRPOU
    passport_series: Mapped[str | None] = mapped_column(String(2))
    passport_number: Mapped[str | None] = mapped_column(String(9))
    birth_date: Mapped[date | None] = mapped_column(Date)

    # -- Status --
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    is_bankrupt: Mapped[bool] = mapped_column(default=False, index=True)
    bankruptcy_case_number: Mapped[str | None] = mapped_column(String(50))

    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # -- Relations --
    portfolio_links: Mapped[list["PortfolioDebtorLink"]] = relationship(back_populates="debtor")
    addresses: Mapped[list["DebtorAddress"]] = relationship(back_populates="debtor")
    contacts: Mapped[list["DebtorContact"]] = relationship(back_populates="debtor")
    court_cases: Mapped[list["CourtCase"]] = relationship(back_populates="debtor")
    registry_checks: Mapped[list["RegistryCheck"]] = relationship(back_populates="debtor")
    enforcement_proceedings: Mapped[list["EnforcementProceeding"]] = relationship(
        back_populates="debtor"
    )


class DebtorAddress(Base):
    """Debtor address (registration, actual, correspondence)."""

    __tablename__ = "debtor_addresses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    debtor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("debtors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    address_type: Mapped[str] = mapped_column(String(30), default="registration")
    region: Mapped[str | None] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
    street: Mapped[str | None] = mapped_column(String(200))
    building: Mapped[str | None] = mapped_column(String(20))
    apartment: Mapped[str | None] = mapped_column(String(20))
    postal_code: Mapped[str | None] = mapped_column(String(10))
    full_address: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    debtor: Mapped["Debtor"] = relationship(back_populates="addresses")


class DebtorContact(Base):
    """Debtor contact information (phone, email)."""

    __tablename__ = "debtor_contacts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    debtor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("debtors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_type: Mapped[str] = mapped_column(String(20))  # phone / email
    value: Mapped[str] = mapped_column(String(200), nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    debtor: Mapped["Debtor"] = relationship(back_populates="contacts")
