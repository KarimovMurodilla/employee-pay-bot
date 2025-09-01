"""User repository file."""

from decimal import Decimal

from sqlalchemy import and_, extract, func, select

from src.bot.structures.role import Role
from src.db.models import User
from src.db.models.transaction import Transaction, TransactionStatus, TransactionType
from src.db.models.user import UserRole

from .base import BaseRepository


class UserRepo(BaseRepository):
    """User repository for CRUD and other SQL queries."""

    async def new(
        self,
        user_id: int,
        user_name: str | None = None,
        first_name: str | None = None,
        second_name: str | None = None,
        is_premium: bool | None = False,
        role: Role | None = Role.USER,
    ) -> None:
        """Insert a new user into the database.

        :param user_id: Telegram user id
        :param user_name: Telegram username
        :param first_name: Telegram profile first name
        :param second_name: Telegram profile second name
        :param language_code: Telegram profile language code
        :param is_premium: Telegram user premium status
        :param role: User's role
        :param user_chat: Telegram chat with user.
        """
        await self.session.merge(
            User(
                user_id=user_id,
                user_name=user_name,
                first_name=first_name,
                second_name=second_name,
                is_premium=is_premium,
                role=role,
            )
        )
        await self.session.commit()

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Get user by telegram ID."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_role(self, role: UserRole) -> list[User]:
        """Get all users by role."""
        result = await self.session.execute(select(User).where(User.role == role))
        return result.scalars().all()

    async def get_by_department(self, department_id: int) -> list[User]:
        """Get all users in department."""
        result = await self.session.execute(
            select(User).where(User.department_id == department_id)
        )
        return result.scalars().all()

    async def get_today_spent(self, user_id: int) -> Decimal:
        """Get amount spent by user today."""
        result = await self.session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.type == TransactionType.PAYMENT,
                    Transaction.status == TransactionStatus.COMPLETED,
                    func.date(Transaction.created_at) == func.current_date(),
                )
            )
        )
        return Decimal(str(result.scalar() or 0))

    async def get_month_spent(self, user_id: int) -> Decimal:
        """Get amount spent by user this month."""
        result = await self.session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.type == TransactionType.PAYMENT,
                    Transaction.status == TransactionStatus.COMPLETED,
                    extract("month", Transaction.created_at)
                    == extract("month", func.current_date()),
                    extract("year", Transaction.created_at)
                    == extract("year", func.current_date()),
                )
            )
        )
        return Decimal(str(result.scalar() or 0))
