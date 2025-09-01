"""User repository file."""

from datetime import datetime

from sqlalchemy import select

from src.db.models.transaction import Transaction, TransactionStatus

from .base import BaseRepository


class TransactionRepo(BaseRepository):
    """Repository for Transaction operations."""

    async def get_user_transactions(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> list[Transaction]:
        """Get user transactions with pagination."""
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_establishment_transactions(
        self,
        establishment_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        """Get establishment transactions with optional date filtering."""
        query = select(Transaction).where(
            Transaction.establishment_id == establishment_id
        )

        if start_date:
            query = query.where(Transaction.created_at >= start_date)
        if end_date:
            query = query.where(Transaction.created_at <= end_date)

        query = (
            query.order_by(Transaction.created_at.desc()).limit(limit).offset(offset)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_pending_transactions(self) -> list[Transaction]:
        """Get all pending transactions."""
        result = await self.session.execute(
            select(Transaction).where(Transaction.status == TransactionStatus.PENDING)
        )
        return result.scalars().all()

    async def _get_transactions_by_user_and_establishment(
        self, user_id: int, establishment_id: int
    ) -> list[Transaction]:
        """Get today's transactions for a user and establishment."""
        result = await self.session.execute(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.establishment_id == establishment_id,
            )
        )
        return result.scalars().all()
    
    async def _get_user_and_establishment_transactions_by_today(
        self, user_id: int, establishment_id: int
    ) -> list[Transaction]:
        """Get today's transactions for a user and establishment."""
        today = datetime.now().date()
        result = await self.session.execute(
            select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.establishment_id == establishment_id,
                Transaction.created_at >= today
            )
        )
        return result.scalars().all()
