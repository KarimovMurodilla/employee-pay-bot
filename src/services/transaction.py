from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.establishment import Establishment
from src.db.models.transaction import Transaction, TransactionStatus, TransactionType
from src.db.models.user import User
from src.errors.custom import InsufficientFundsError, ValidationError
from src.repositories.establishment import EstablishmentRepo
from src.repositories.transaction import TransactionRepo
from src.repositories.user import UserRepo
from src.schemas.balance import PaymentRequest, PaymentResult


class TransactionService:
    """Service for transaction processing."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepo(session)
        self.establishment_repo = EstablishmentRepo(session)
        self.transaction_repo = TransactionRepo(session)

    async def process_payment(self, payment_request: PaymentRequest) -> PaymentResult:
        """Process a payment transaction with full validation."""
        try:
            # Validate user
            user = await self.user_repo.get_by_id(User, payment_request.user_id)
            if not user or not user.is_active:
                return PaymentResult(
                    success=False, error_message="User not found or inactive"
                )

            # Validate establishment
            establishment = await self.establishment_repo.get_by_id(
                Establishment, payment_request.establishment_id
            )
            if not establishment or not establishment.is_active:
                return PaymentResult(
                    success=False, error_message="Establishment not found or inactive"
                )

            # Validate amount
            if payment_request.amount <= 0:
                return PaymentResult(
                    success=False, error_message="Payment amount must be positive"
                )

            # Check establishment limits
            if (
                establishment.max_order_amount > 0
                and payment_request.amount > establishment.max_order_amount
            ):
                return PaymentResult(
                    success=False,
                    error_message=f"Amount exceeds establishment "
                    f"limit of {establishment.max_order_amount}",
                )

            # Check user balance
            if user.balance < payment_request.amount:
                return PaymentResult(success=False, error_message="Insufficient funds")

            # Check daily limit
            today_spent = await self.user_repo.get_today_spent(payment_request.user_id)
            if (
                user.daily_limit > 0
                and (today_spent + payment_request.amount) > user.daily_limit
            ):
                return PaymentResult(
                    success=False,
                    error_message=f"Daily spending limit exceeded. Remaining: "
                    f"{user.daily_limit - today_spent}",
                )

            # Check monthly limit
            month_spent = await self.user_repo.get_month_spent(payment_request.user_id)
            if (
                user.monthly_limit > 0
                and (month_spent + payment_request.amount) > user.monthly_limit
            ):
                return PaymentResult(
                    success=False,
                    error_message=f"Monthly spending limit exceeded. Remaining: "
                    f"{user.monthly_limit - month_spent}",
                )

            # Create transaction
            transaction = Transaction(
                user_id=payment_request.user_id,
                establishment_id=payment_request.establishment_id,
                amount=payment_request.amount,
                type=TransactionType.PAYMENT,
                status=TransactionStatus.PENDING,
                description=payment_request.description,
                receipt_data=payment_request.receipt_data,
            )

            transaction = await self.transaction_repo.create(transaction)

            # Process the payment
            await self._complete_transaction(transaction)

            # Send notification to establishment
            await self.notification_service.send_payment_notification(
                establishment.owner_telegram_id, transaction
            )

            return PaymentResult(
                success=True,
                transaction_id=transaction.id,
                balance_after=user.balance - payment_request.amount,
            )

        except Exception as e:
            await self.session.rollback()
            return PaymentResult(
                success=False, error_message=f"Payment processing failed: {str(e)}"
            )

    async def _complete_transaction(self, transaction: Transaction):
        """Complete a transaction and update user balance."""
        # Get current user balance
        user = await self.user_repo.get_by_id(User, transaction.user_id)
        if not user:
            raise ValidationError(f"User with id {transaction.user_id} not found")

        old_balance = user.balance

        # Calculate balance change based on transaction type
        if transaction.type == TransactionType.PAYMENT:
            balance_change = -transaction.amount
        elif transaction.type in [
            TransactionType.REFUND,
            TransactionType.BALANCE_TOP_UP,
            TransactionType.BALANCE_ADJUSTMENT,
        ]:
            balance_change = transaction.amount
        else:
            raise ValidationError(f"Invalid transaction type: {transaction.type}")

        new_balance = old_balance + balance_change

        # Prevent negative balance for payments
        if transaction.type == TransactionType.PAYMENT and new_balance < 0:
            raise InsufficientFundsError("Insufficient funds for transaction")

        # Update user balance
        user.balance = new_balance
        user.updated_at = func.current_timestamp()
        await self.user_repo.update(user)

        # Update transaction status
        transaction.status = TransactionStatus.COMPLETED
        transaction.updated_at = func.current_timestamp()
        await self.transaction_repo.update(transaction)

    async def process_refund(
        self, transaction_id: int, admin_id: int, reason: str | None = None
    ) -> PaymentResult:
        """Process a refund for a completed payment."""
        try:
            # Get original transaction
            original_transaction = await self.transaction_repo.get_by_id(
                Transaction, transaction_id
            )
            if not original_transaction:
                return PaymentResult(
                    success=False, error_message="Original transaction not found"
                )

            if original_transaction.type != TransactionType.PAYMENT:
                return PaymentResult(
                    success=False, error_message="Can only refund payment transactions"
                )

            if original_transaction.status != TransactionStatus.COMPLETED:
                return PaymentResult(
                    success=False,
                    error_message="Can only refund completed transactions",
                )

            # Create refund transaction
            refund_transaction = Transaction(
                user_id=original_transaction.user_id,
                establishment_id=original_transaction.establishment_id,
                amount=original_transaction.amount,
                type=TransactionType.REFUND,
                status=TransactionStatus.PENDING,
                description=f"Refund for transaction #{transaction_id}. "
                f"Reason: {reason or 'No reason provided'}",
                created_by=admin_id,
            )

            refund_transaction = await self.transaction_repo.create(refund_transaction)

            # Process the refund
            await self._complete_transaction(refund_transaction)

            user = await self.user_repo.get_by_id(User, original_transaction.user_id)

            return PaymentResult(
                success=True,
                transaction_id=refund_transaction.id,
                balance_after=user.balance,
            )

        except Exception as e:
            await self.session.rollback()
            return PaymentResult(
                success=False, error_message=f"Refund processing failed: {str(e)}"
            )

    async def get_transaction_by_id(self, transaction_id: int) -> Transaction | None:
        """Get transaction by ID."""
        return await self.transaction_repo.get_by_id(Transaction, transaction_id)

    async def get_user_and_establishment_transactions_by_today(
        self, user_id: int, establishment_id: int
    ) -> list[Transaction]:
        """Get today's transactions for a user and establishment."""
        return await self.transaction_repo._get_user_and_establishment_transactions_by_today(
            user_id, establishment_id
        )

    async def get_transactions_by_user_and_establishment(
        self, user_id: int, establishment_owner_telegram_id: int
    ) -> list[Transaction]:
        """Get today's transactions for a user and establishment."""
        establishment = await self.establishment_repo.get_by_owner_telegram_id(
            establishment_owner_telegram_id
        )
        return await self.transaction_repo._get_transactions_by_user_and_establishment(
            user_id, establishment.id
        )

    # async def get_transactions_by_date(self, establishment_owner_id: int, start_date: datetime, end_date: datetime, limit: int, offset: int):
    #     transactions = await self.transaction_repo.get_establishment_transactions(
    #         establishment_id=establishment_id,
    #         start_date=start_date,
    #         end_date=end_date,
    #         limit=limit,
    #         offset=offset
    #     )
    #     return transactions
