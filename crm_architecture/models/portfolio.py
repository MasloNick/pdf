"""
Portfolio entity — a purchased package of debt claims.
"""

from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Text
from sqlalchemy.orm import relationship

from .credit_case import Base


class Portfolio(Base):
    """A purchased package of debt rights with acquisition parameters."""

    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    seller = Column(String(255), nullable=False)
    purchase_date = Column(Date, nullable=False)
    total_face_value = Column(Numeric(16, 2), nullable=False)
    purchase_price = Column(Numeric(16, 2), nullable=False)
    case_count = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # --- Relationships ---
    cases = relationship("CreditCase", back_populates="portfolio")

    @property
    def discount_rate(self) -> float:
        """Purchase discount as a percentage of face value."""
        if self.total_face_value and self.total_face_value > 0:
            return float(
                (self.total_face_value - self.purchase_price) / self.total_face_value * 100
            )
        return 0.0
