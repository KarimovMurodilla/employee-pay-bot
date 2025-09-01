from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class Establishment(Base):
    __tablename__ = "establishments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    qr_code: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    owner_telegram_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id")
    )
    max_order_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), default=Decimal("0.00")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    owner: Mapped[Optional["User"]] = relationship(
        "User", back_populates="owned_establishments", lazy="joined"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", back_populates="establishment"
    )

    # Indexes
    __table_args__ = (Index("idx_establishments_qr_code", "qr_code"),)

    def __repr__(self) -> str:
        return f"<Establishment(id={self.id}, name='{self.name}', owner_telegram_id={self.owner_telegram_id})>"
