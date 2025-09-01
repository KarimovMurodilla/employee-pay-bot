from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    recipient_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    transaction_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("transactions.id")
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    recipient: Mapped["User"] = relationship("User", back_populates="notifications")
    transaction: Mapped[Optional["Transaction"]] = relationship(
        "Transaction", back_populates="notifications"
    )

    # Indexes
    __table_args__ = (
        Index("idx_notifications_recipient", "recipient_id"),
        Index("idx_notifications_read", "is_read"),
    )
