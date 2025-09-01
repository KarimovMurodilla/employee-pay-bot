"""User repository file."""

from decimal import Decimal

from sqlalchemy import and_, func, select

from src.db.models import Establishment
from src.db.models.transaction import Transaction, TransactionStatus, TransactionType

from .base import BaseRepository


class EstablishmentRepo(BaseRepository):
    """Repository for Establishment operations."""

    async def get_by_qr_code(self, qr_code: str) -> Establishment | None:
        """Get establishment by QR code."""
        result = await self.session.execute(
            select(Establishment).where(Establishment.qr_code == qr_code)
        )
        return result.scalar_one_or_none()

    async def get_by_owner_telegram_id(self, owner_telegram_id: int) -> Establishment | None:
        """Get establishment by QR code."""
        result = await self.session.execute(
            select(Establishment).where(Establishment.owner_telegram_id == owner_telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_active_establishments(self) -> list[Establishment]:
        """Get all active establishments."""
        result = await self.session.execute(
            select(Establishment).where(Establishment.is_active)
        )
        return result.scalars().all()

    async def get_total_revenue(self, establishment_id: int) -> Decimal:
        """Get total revenue for establishment."""
        result = await self.session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    Transaction.establishment_id == establishment_id,
                    Transaction.type == TransactionType.PAYMENT,
                    Transaction.status == TransactionStatus.COMPLETED,
                )
            )
        )
        return Decimal(str(result.scalar() or 0))

    async def get_today_revenue(self, establishment_id: int) -> Decimal:
        """Get today's revenue for establishment."""
        result = await self.session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    Transaction.establishment_id == establishment_id,
                    Transaction.type == TransactionType.PAYMENT,
                    Transaction.status == TransactionStatus.COMPLETED,
                    func.date(Transaction.created_at) == func.current_date(),
                )
            )
        )
        return Decimal(str(result.scalar() or 0))
