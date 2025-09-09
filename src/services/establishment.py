from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.establishment import Establishment
from src.db.models.transaction import Transaction, TransactionStatus, TransactionType
from src.errors.custom import ValidationError
from src.repositories.establishment import EstablishmentRepo
from src.repositories.transaction import TransactionRepo
from src.utils.excel_write import write_revenue_excel
from src.utils.pdf_write import write_revenue_pdf
from pathlib import Path


class EstablishmentService:
    """Service for establishment operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.establishment_repo = EstablishmentRepo(session)
        self.transaction_repo = TransactionRepo(session)

    async def get_establishment_by_qr(self, qr_code: str) -> Establishment | None:
        """Get establishment by QR code."""
        return await self.establishment_repo.get_by_qr_code(qr_code)

    async def get_establishment_by_owner_telegram_id(
        self, owner_telegram_id: int
    ) -> Establishment | None:
        """Get establishment by QR code."""
        return await self.establishment_repo.get_by_owner_telegram_id(owner_telegram_id)

    async def create_establishment(
        self,
        name: str,
        qr_code: str,
        owner_telegram_id: int | None = None,
        description: str | None = None,
        address: str | None = None,
        max_order_amount: Decimal = Decimal("0"),
    ) -> Establishment:
        """Create new establishment."""
        # Check if QR code already exists
        existing = await self.establishment_repo.get_by_qr_code(qr_code)
        if existing:
            raise ValidationError(
                f"Establishment with QR code {qr_code} already exists"
            )

        establishment = Establishment(
            name=name,
            qr_code=qr_code,
            owner_telegram_id=owner_telegram_id,
            description=description,
            address=address,
            max_order_amount=max_order_amount,
        )

        return await self.establishment_repo.create(establishment)

    async def get_establishment_total_revenue(self, establishment_id: int):
        total_revenue = await self.establishment_repo.get_total_revenue(
            establishment_id
        )
        return total_revenue

    async def get_establishment_revenue_summary(
        self, establishment_id: int
    ) -> dict[str, Any]:
        """Get comprehensive revenue summary for establishment."""
        establishment = await self.establishment_repo.get_by_id(
            Establishment, establishment_id
        )
        if not establishment:
            raise ValidationError(f"Establishment with id {establishment_id} not found")

        total_revenue = await self.establishment_repo.get_total_revenue(
            establishment_id
        )
        today_revenue = await self.establishment_repo.get_today_revenue(
            establishment_id
        )

        # Get transaction count
        result = await self.session.execute(
            select(func.count(Transaction.id)).where(
                and_(
                    Transaction.establishment_id == establishment_id,
                    Transaction.type == TransactionType.PAYMENT,
                    Transaction.status == TransactionStatus.COMPLETED,
                )
            )
        )
        total_orders = result.scalar() or 0

        return {
            "establishment_id": establishment_id,
            "name": establishment.name,
            "total_revenue": total_revenue,
            "today_revenue": today_revenue,
            "total_orders": total_orders,
            "average_order_value": total_revenue / total_orders
            if total_orders > 0
            else Decimal("0"),
        }

    async def get_establishment_transactions(
        self,
        establishment_owner_telegram_id: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Transaction]:
        """Get establishment transactions with filtering."""
        establishment = await self.establishment_repo.get_by_owner_telegram_id(
            establishment_owner_telegram_id
        )
        return await self.transaction_repo.get_establishment_transactions(
            establishment.id, start_date, end_date, limit, offset
        )

    async def get_revenue_summary_in_pdf(self, establishment_id: int):
        """Generate revenue summary report in PDF format."""
        summary = await self.get_establishment_revenue_summary(establishment_id)
        reports_dir = Path(__file__).parent.parent.parent / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        pdf_filename = reports_dir / f"revenue-summary_{datetime.now().strftime('%d-%m-%Y %H-%M-%S')}.pdf"
        result = write_revenue_pdf(data=summary, filename=str(pdf_filename))
        if result:
            return str(pdf_filename)

    async def get_revenue_summary_in_excel(self, establishment_id: int):
        """Generate revenue summary report in XLSX format."""

        summary = await self.get_establishment_revenue_summary(establishment_id)
        reports_dir = Path(__file__).parent.parent.parent / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        xlsx_filename = reports_dir / f"revenue-summary_{datetime.now().strftime('%d-%m-%Y %H-%M-%S')}.xlsx"
        result = write_revenue_excel(data=summary, filename=str(xlsx_filename))
        if result:
            return str(xlsx_filename)
