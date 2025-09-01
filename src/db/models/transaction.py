import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class TransactionType(enum.Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    BALANCE_TOP_UP = "balance_top_up"
    BALANCE_ADJUSTMENT = "balance_adjustment"


class TransactionStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    establishment_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("establishments.id")
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType), default=TransactionType.PAYMENT, nullable=False
    )
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text)
    receipt_data: Mapped[dict | None] = mapped_column(JSONB)
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="transactions"
    )
    creator: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[created_by], back_populates="created_transactions"
    )
    establishment: Mapped[Optional["Establishment"]] = relationship(
        "Establishment", back_populates="transactions", lazy="joined"
    )
    balance_history: Mapped[Optional["BalanceHistory"]] = relationship(
        "BalanceHistory", back_populates="transaction"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="transaction"
    )

    # Indexes
    __table_args__ = (
        Index("idx_transactions_user_id", "user_id"),
        Index("idx_transactions_establishment_id", "establishment_id"),
        Index("idx_transactions_created_at", "created_at"),
        Index("idx_transactions_type_status", "type", "status"),
    )
