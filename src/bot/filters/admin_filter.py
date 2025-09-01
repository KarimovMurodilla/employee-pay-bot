from aiogram.filters import BaseFilter
from aiogram.types import Message

from src.configuration import conf


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message, *args, **kwargs):
        if message.from_user.id in conf.ADMINS:
            return True
