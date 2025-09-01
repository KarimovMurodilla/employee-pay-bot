from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class BalanceHistory(Base):
    __tablename__ = "balance_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    transaction_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("transactions.id")
    )
    amount_change: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    balance_before: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp()
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="balance_history"
    )
    creator: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[created_by], back_populates="created_balance_changes"
    )
    transaction: Mapped[Optional["Transaction"]] = relationship(
        "Transaction", back_populates="balance_history"
    )

    # Indexes
    __table_args__ = (
        Index("idx_balance_history_user_id", "user_id"),
        Index("idx_balance_history_created_at", "created_at"),
    )
