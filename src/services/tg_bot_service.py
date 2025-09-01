from sqlalchemy.ext.asyncio import AsyncSession

from src.services.balance import BalanceService
from src.services.establishment import EstablishmentService
from src.services.notification import NotificationService
from src.services.report import ReportService
from src.services.transaction import TransactionService
from src.services.user import UserService


class TelegramBotService:
    """Main service class that aggregates all other services."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service = UserService(session)
        self.transaction_service = TransactionService(session)
        self.balance_service = BalanceService(session)
        self.establishment_service = EstablishmentService(session)
        self.notification_service = NotificationService(session)
        self.report_service = ReportService(session)
