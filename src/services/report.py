from decimal import Decimal
from typing import Any

from sqlalchemy import and_, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.transaction import Transaction, TransactionStatus, TransactionType
from src.db.models.user import User, UserRole
from src.repositories.establishment import EstablishmentRepo
from src.repositories.transaction import TransactionRepo
from src.repositories.user import UserRepo


class ReportService:
    """Service for report generation and analytics."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepo(session)
        self.establishment_repo = EstablishmentRepo(session)
        self.transaction_repo = TransactionRepo(session)

    async def get_company_summary(self) -> dict[str, Any]:
        """Get overall company spending summary."""
        # Total spending
        result = await self.session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    Transaction.type == TransactionType.PAYMENT,
                    Transaction.status == TransactionStatus.COMPLETED,
                )
            )
        )
        total_spending = Decimal(str(result.scalar() or 0))

        # Today's spending
        result = await self.session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    Transaction.type == TransactionType.PAYMENT,
                    Transaction.status == TransactionStatus.COMPLETED,
                    func.date(Transaction.created_at) == func.current_date(),
                )
            )
        )
        today_spending = Decimal(str(result.scalar() or 0))

        # This month's spending
        result = await self.session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    Transaction.type == TransactionType.PAYMENT,
                    Transaction.status == TransactionStatus.COMPLETED,
                    extract("month", Transaction.created_at)
                    == extract("month", func.current_date()),
                    extract("year", Transaction.created_at)
                    == extract("year", func.current_date()),
                )
            )
        )
        month_spending = Decimal(str(result.scalar() or 0))

        # Active users count
        result = await self.session.execute(
            select(func.count(User.id)).where(
                and_(User.is_active, User.role == UserRole.EMPLOYEE)
            )
        )
        active_users = result.scalar() or 0

        return {
            "total_spending": total_spending,
            "today_spending": today_spending,
            "month_spending": month_spending,
            "active_users": active_users,
        }

    async def get_establishment_breakdown(self) -> list[dict[str, Any]]:
        """Get spending breakdown by establishment."""
        query = """
        SELECT
            e.id,
            e.name,
            COALESCE(SUM(t.amount), 0) as total_revenue,
            COUNT(t.id) as total_orders,
            COALESCE(SUM(CASE WHEN DATE(t.created_at) =
            CURRENT_DATE THEN t.amount ELSE 0 END), 0) as today_revenue
        FROM establishments e
        LEFT JOIN transactions t ON e.id = t.establishment_id
            AND t.type = 'payment'
            AND t.status = 'completed'
        GROUP BY e.id, e.name
        ORDER BY total_revenue DESC
        """

        result = await self.session.execute(query)
        establishments = []

        for row in result:
            establishments.append(
                {
                    "establishment_id": row.id,
                    "name": row.name,
                    "total_revenue": Decimal(str(row.total_revenue or 0)),
                    "total_orders": row.total_orders or 0,
                    "today_revenue": Decimal(str(row.today_revenue or 0)),
                }
            )

        return establishments

    async def get_department_breakdown(self) -> list[dict[str, Any]]:
        """Get spending breakdown by department."""
        query = """
        SELECT
            d.id,
            d.name,
            COUNT(DISTINCT u.id) as employee_count,
            COALESCE(SUM(t.amount), 0) as total_spending,
            COALESCE(SUM(CASE WHEN DATE(t.created_at) =
            CURRENT_DATE THEN t.amount ELSE 0 END), 0) as today_spending
        FROM departments d
        LEFT JOIN users u ON d.id = u.department_id AND u.role = 'employee'
        LEFT JOIN transactions t ON u.id = t.user_id
            AND t.type = 'payment'
            AND t.status = 'completed'
        GROUP BY d.id, d.name
        ORDER BY total_spending DESC
        """

        result = await self.session.execute(query)
        departments = []

        for row in result:
            departments.append(
                {
                    "department_id": row.id,
                    "name": row.name,
                    "employee_count": row.employee_count or 0,
                    "total_spending": Decimal(str(row.total_spending or 0)),
                    "today_spending": Decimal(str(row.today_spending or 0)),
                }
            )

        return departments
