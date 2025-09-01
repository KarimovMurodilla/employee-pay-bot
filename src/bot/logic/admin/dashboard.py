from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot.filters.admin_filter import AdminFilter
from src.cache import Cache
from src.language.translator import LocalizedTranslator

from .router import admin_router


@admin_router.message(F.text == "/admin", AdminFilter())
async def process_registration(
    message: Message, state: FSMContext, translator: LocalizedTranslator, cache: Cache
):
    await message.answer("Welcome to admin panel")
