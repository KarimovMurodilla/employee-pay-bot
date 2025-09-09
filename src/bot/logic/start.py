"""This file represents a start logic."""

from aiogram import Router, types
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext

from src.bot.structures.fsm.establishment import ProcessEstablishment
from src.bot.structures.fsm.user import ProcessUser
from src.bot.structures.keyboards import common
from src.db.models.user import UserRole
from src.services.tg_bot_service import TelegramBotService

start_router = Router(name="start")


@start_router.message(CommandStart(deep_link=True))
async def start_handler(
    message: types.Message,
    command: CommandObject,
    db: TelegramBotService,
    state: FSMContext,
):
    """Start command handler."""
    await state.clear()
    qr_code = command.args

    user = await db.user_service.get_user_by_telegram_id(message.from_user.id)
    if not user:
        user = await db.user_service.create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )

    establishment = await db.establishment_service.get_establishment_by_qr(qr_code)
    if not establishment:
        return message.answer("Bunday muassasa topilmadi")

    # transactions = (
    #     await db.transaction_service.get_user_and_establishment_transactions_by_today(
    #         user_id=user.id, establishment_id=establishment.id
    #     )
    # )
    today_spent = await db.user_service.get_user_today_spent(message.from_user.id)

    if today_spent:
        return message.answer("Sizning kunlik limitingiz tugagan")

    text = f"🏢 Muassasa: {establishment.name}\n"
    text += f"🏪 Muassasa uchun limit: {establishment.max_order_amount}\n"
    text += f"💳 Umumiy balansingiz: {user.balance}\n\n"
    text += "To'lo'v summasini kiriting"
    await message.answer(text)
    await state.set_data(dict(qr_code=qr_code))
    await state.set_state(ProcessUser.confirm_purchase)


@start_router.message(CommandStart())
async def start_handler(
    message: types.Message,
    db: TelegramBotService,
    state: FSMContext,
):
    await state.clear()

    user = await db.user_service.get_user_by_telegram_id(message.from_user.id)
    if not user:
        new_user = await db.user_service.create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        print("New user created:", new_user)

        return await message.answer("Assalomu aleykum")

    if user.role == UserRole.EMPLOYEE:
        await state.set_state(ProcessUser.select_menu)
        return await message.answer("Assalomu aleykum", reply_markup=common.user_menu())

    elif user.role == UserRole.ESTABLISHMENT:
        await state.set_state(ProcessEstablishment.select_menu)
        return await message.answer(
            "Assalomu aleykum", reply_markup=common.establishment_menu()
        )
