from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.notification import Notification
from src.db.models.transaction import Transaction
from src.db.models.user import User
from src.repositories.notification import NotificationRepo
from src.repositories.user import UserRepo


class NotificationService:
    """Service for notification management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_repo = NotificationRepo(session)
        self.user_repo = UserRepo(session)

    async def send_payment_notification(
        self, recipient_id: int | None, transaction: Transaction
    ):
        """Send payment notification to establishment owner."""
        if not recipient_id:
            return  # No owner to notify

        user = await self.user_repo.get_by_id(User, transaction.user_id)
        if not user:
            return

        notification = Notification(
            recipient_id=recipient_id,
            transaction_id=transaction.id,
            title="💳 New Payment Received",
            message=f"🧾 Payment from {user.full_name} (ID: {user.telegram_id})\n"
            f"Amount: {transaction.amount:,.0f} sum\n"
            f"Date: {transaction.created_at.strftime('%d.%m.%Y %H:%M')}",
        )

        await self.notification_repo.create(notification)

    async def get_user_notifications(
        self, user_id: int, unread_only: bool = False
    ) -> list[Notification]:
        """Get notifications for user."""
        return await self.notification_repo.get_user_notifications(user_id, unread_only)

    async def mark_notifications_read(self, notification_ids: list[int]):
        """Mark notifications as read."""
        await self.notification_repo.mark_as_read(notification_ids)
