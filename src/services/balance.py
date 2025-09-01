from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.transaction import Transaction, TransactionStatus, TransactionType
from src.db.models.user import User, UserRole
from src.repositories.transaction import TransactionRepo
from src.repositories.user import UserRepo
from src.schemas.balance import BalanceTopUpRequest, PaymentResult

from .transaction import TransactionService


class BalanceService:
    """Service for balance management operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepo(session)
        self.transaction_repo = TransactionRepo(session)
        self.transaction_service = TransactionService(session)

    async def top_up_balance(self, request: BalanceTopUpRequest) -> PaymentResult:
        """Top up user balance."""
        try:
            # Validate user
            user = await self.user_repo.get_by_id(User, request.user_id)
            if not user:
                return PaymentResult(success=False, error_message="User not found")

            # Validate admin
            admin = await self.user_repo.get_by_id(User, request.admin_id)
            if not admin or admin.role != UserRole.ADMIN:
                return PaymentResult(
                    success=False, error_message="Only admins can top up balances"
                )

            # Validate amount
            if request.amount <= 0:
                return PaymentResult(
                    success=False, error_message="Top-up amount must be positive"
                )

            # Create top-up transaction
            transaction = Transaction(
                user_id=request.user_id,
                amount=request.amount,
                type=TransactionType.BALANCE_TOP_UP,
                status=TransactionStatus.PENDING,
                description=request.description
                or f"Balance top-up by admin {admin.full_name}",
                created_by=request.admin_id,
            )

            transaction = await self.transaction_repo.create(transaction)

            # Process the top-up
            await self.transaction_service._complete_transaction(transaction)

            user = await self.user_repo.get_by_id(User, request.user_id)

            return PaymentResult(
                success=True, transaction_id=transaction.id, balance_after=user.balance
            )

        except Exception as e:
            await self.session.rollback()
            return PaymentResult(
                success=False, error_message=f"Balance top-up failed: {str(e)}"
            )

    async def adjust_balance(
        self, user_id: int, amount: Decimal, admin_id: int, description: str
    ) -> PaymentResult:
        """Manually adjust user balance (can be positive or negative)."""
        try:
            # Validate user
            user = await self.user_repo.get_by_id(User, user_id)
            if not user:
                return PaymentResult(success=False, error_message="User not found")

            # Validate admin
            admin = await self.user_repo.get_by_id(User, admin_id)
            if not admin or admin.role != UserRole.ADMIN:
                return PaymentResult(
                    success=False, error_message="Only admins can adjust balances"
                )

            # Check if adjustment would result in negative balance
            if user.balance + amount < 0:
                return PaymentResult(
                    success=False,
                    error_message="Balance adjustment would result in negative balance",
                )

            # Create adjustment transaction
            transaction = Transaction(
                user_id=user_id,
                amount=abs(amount),  # Store absolute value
                type=TransactionType.BALANCE_ADJUSTMENT,
                status=TransactionStatus.PENDING,
                description=f"Balance adjustment by admin "
                f"{admin.full_name}: {description}",
                created_by=admin_id,
            )

            transaction = await self.transaction_repo.create(transaction)

            # For negative adjustments, we need to handle them specially
            if amount < 0:
                # Temporarily change amount to negative for processing
                transaction.amount = amount

            # Process the adjustment
            await self.transaction_service._complete_transaction(transaction)

            user = await self.user_repo.get_by_id(User, user_id)

            return PaymentResult(
                success=True, transaction_id=transaction.id, balance_after=user.balance
            )

        except Exception as e:
            await self.session.rollback()
            return PaymentResult(
                success=False, error_message=f"Balance adjustment failed: {str(e)}"
            )
