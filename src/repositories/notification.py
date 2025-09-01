"""User repository file."""

from sqlalchemy import select, update

from src.db.models import Notification

from .base import BaseRepository


class NotificationRepo(BaseRepository):
    """Repository for Notification operations."""

    async def get_user_notifications(
        self, user_id: int, unread_only: bool = False
    ) -> list[Notification]:
        """Get user notifications."""
        query = select(Notification).where(Notification.recipient_id == user_id)

        if unread_only:
            query = query.where(not Notification.is_read)

        query = query.order_by(Notification.created_at.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def mark_as_read(self, notification_ids: list[int]):
        """Mark notifications as read."""
        await self.session.execute(
            update(Notification)
            .where(Notification.id.in_(notification_ids))
            .values(is_read=True)
        )
