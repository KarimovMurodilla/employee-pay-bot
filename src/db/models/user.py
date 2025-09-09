import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.models.base import Base


class UserRole(enum.Enum):
    EMPLOYEE = "employee"
    ESTABLISHMENT = "establishment"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False
    )
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.EMPLOYEE, nullable=False
    )
    department_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("departments.id")
    )
    balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    department: Mapped[Optional["Department"]] = relationship(
        "Department", back_populates="users"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction", foreign_keys="Transaction.user_id", back_populates="user", cascade="all, delete-orphan"
    )
    establishments: Mapped[list["Establishment"]] = relationship(
        "Establishment",
        back_populates="owner"
    )

    # Indexes
    __table_args__ = (
        Index("idx_users_telegram_id", "telegram_id"),
        Index("idx_users_role", "role"),
        Index("idx_users_department", "department_id"),
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username or f"User {self.telegram_id}"

    def __repr__(self):
        return f"User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})"
