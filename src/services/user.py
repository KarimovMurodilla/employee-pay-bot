from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.transaction import Transaction, TransactionStatus
from src.db.models.user import User, UserRole
from src.errors.custom import ValidationError
from src.repositories.transaction import TransactionRepo
from src.repositories.user import UserRepo


class UserService:
    """Service for user-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepo(session)
        self.transaction_repo = TransactionRepo(session)

    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        """Get user by telegram ID."""
        return await self.user_repo.get_by_telegram_id(telegram_id)

    async def create_user(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        role: UserRole = UserRole.EMPLOYEE,
        department_id: int | None = None,
        daily_limit: Decimal = Decimal("100000"),
        monthly_limit: Decimal = Decimal("2000000"),
    ) -> User:
        """Create new user."""

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            role=role,
            department_id=department_id,
            daily_limit=daily_limit,
            monthly_limit=monthly_limit,
        )

        return await self.user_repo.create(user)

    async def update_user_limits(
        self,
        user_id: int,
        daily_limit: Decimal | None = None,
        monthly_limit: Decimal | None = None,
    ) -> User:
        """Update user spending limits."""
        user = await self.user_repo.get_by_id(User, user_id)
        if not user:
            raise ValidationError(f"User with id {user_id} not found")

        if daily_limit is not None:
            user.daily_limit = daily_limit
        if monthly_limit is not None:
            user.monthly_limit = monthly_limit

        return await self.user_repo.update(user)

    async def get_user_today_spent(self, telegram_id: int):
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise ValidationError(f"User with id {telegram_id} not found")
        today_spent = await self.user_repo.get_today_spent(user.id)
        return today_spent

    async def get_user_spending_summary(self, telegram_id: int) -> dict[str, Any]:
        """Get comprehensive user spending summary."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise ValidationError(f"User with id {telegram_id} not found")

        today_spent = await self.user_repo.get_today_spent(user.id)
        month_spent = await self.user_repo.get_month_spent(user.id)

        return {
            "user_id": user.id,
            "balance": user.balance,
            "daily_limit": user.daily_limit,
            "monthly_limit": user.monthly_limit,
            "today_spent": today_spent,
            "month_spent": month_spent,
            "daily_remaining": user.daily_limit - today_spent,
            "monthly_remaining": user.monthly_limit - month_spent,
            "can_spend_today": user.daily_limit > today_spent,
            "can_spend_this_month": user.monthly_limit > month_spent,
        }

    async def get_user_transactions(
        self, telegram_id: int, limit: int = 100, offset: int = 0
    ) -> list[Transaction]:
        """Get user transaction history."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        return await self.transaction_repo.get_user_transactions(user.id, limit, offset)

    async def withdraw_from_balance(
        self, telegram_id: int, establishment_id: int, amount: Decimal
    ) -> Transaction:
        """Withdraw amount from user balance."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise ValidationError(f"User with id {telegram_id} not found")
        if user.balance < amount:
            raise ValidationError("Insufficient balance")
        user.balance -= amount

        transaction = Transaction(
            user_id=user.id,
            amount=amount,
            description="Withdrawal",
            establishment_id=establishment_id,  # Assuming no establishment for withdrawals
            status=TransactionStatus.COMPLETED,
        )
        await self.transaction_repo.create(transaction)
        await self.user_repo.update(user)

        return transaction
