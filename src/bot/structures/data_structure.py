"""Data Structures.

This file contains TypedDict structure to store data which will
transfer throw Dispatcher->Middlewares->Handlers.
"""

from typing import TypedDict

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncEngine

from src.bot.structures.role import Role
from src.language.enums import Locales
from src.language.translator import LocalizedTranslator, Translator
from src.services.tg_bot_service import TelegramBotService


class TransferData(TypedDict):
    """Common transfer data."""

    translator: Translator | LocalizedTranslator
    engine: AsyncEngine
    db: TelegramBotService
    bot: Bot
    role: Role


class TransferUserData(TypedDict):
    role: Role
    locale: Locales
