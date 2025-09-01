from aiogram import F, types
from aiogram.fsm.context import FSMContext

from src.bot.structures.fsm.user import ProcessUser
from src.services.tg_bot_service import TelegramBotService
from src.bot.structures.keyboards import common

from .router import user_router
from datetime import datetime


@user_router.message(ProcessUser.select_menu, F.text == "Tranzaksiyalar")
async def start_handler(
    message: types.Message,
    db: TelegramBotService,
    state: FSMContext,
):
    user_transactions = await db.user_service.get_user_transactions(
        telegram_id=message.from_user.id,
    )
    
    transactions_message = ""
    if not user_transactions:
        transactions_message += "Tranzaksiyalar topilmadi."
    else:
        transactions_message += "Sizning tranzaksiyalaringiz:\n\n"
        for transaction in user_transactions:
            transactions_message += (
                f"ID: {transaction.id}\n"
                f"Summa: {transaction.amount} сум\n"
                f"Muassasa: {transaction.establishment.name}\n"
                f"Vaqt: {transaction.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
    await message.answer(transactions_message)


@user_router.message(ProcessUser.select_menu, F.text == "Mening hisobim")
async def start_handler(
    message: types.Message,
    db: TelegramBotService,
    state: FSMContext,
):
    user_spending_summary = await db.user_service.get_user_spending_summary(
        telegram_id=message.from_user.id,
    )
    summary_message = (
        f"Hisobingiz: {user_spending_summary['balance']} сум\n"
        f"Kunlik sarflangan: {user_spending_summary['today_spent']} сум\n"
        f"Oylik sarflangan: {user_spending_summary['month_spent']} сум\n"
    )
    await message.answer(summary_message)


@user_router.message(ProcessUser.confirm_purchase, F.text)
async def confirm_purchase(
    message: types.Message,
    db: TelegramBotService,
    state: FSMContext,
):
    if not message.text.isdigit():
        await message.answer("Iltimos faqat son kiriting")

    else:
        amount = int(message.text)
        qr_code = await state.get_value("qr_code")
        user = await db.user_service.get_user_by_telegram_id(message.from_user.id)
        today_spent = await db.user_service.get_user_today_spent(message.from_user.id)
        establishment = await db.establishment_service.get_establishment_by_qr(qr_code)
        transactions = await db.transaction_service.get_user_and_establishment_transactions_by_today(
            user_id=user.id,
            establishment_id=establishment.id
        )

        total_amount = sum([transaction.amount for transaction in transactions]) # total spent in this establishment today
        if user.balance < amount:
            await message.answer(f"Hisobingizda yetarli mablag' mavjud emas\n\nSizning hisobingiz: {user.balance}")

        elif establishment.max_order_amount-(total_amount + amount) < 0: # user.daily_limit - (today_spent + amount) < 0
            await message.answer(f"Kiritilgan summa restoran kunlik limitidan oshib ketdi.\n\nSizdagi qolgan limit: {establishment.max_order_amount - total_amount}")

        else:
            await message.answer(
                f"Sizning hisobingiz: {user.balance}\n"
                f"Sizning kunlik limitingiz: {establishment.max_order_amount - total_amount}\n\n" # user.daily_limit - today_spent
                f"To'lov qilingandan kegin hisob: {user.balance - amount}\n"
                f"To'lov qilingandan kegin kunlik limit: {establishment.max_order_amount-(total_amount + amount)}",
                reply_markup=common.accept()
            )
            await state.update_data(dict(amount=amount))
            await state.set_state(ProcessUser.accept_purchase)


@user_router.callback_query(ProcessUser.accept_purchase, F.data == "accept_purchase")
async def confirm_handler(
    c: types.CallbackQuery,
    db: TelegramBotService,
    state: FSMContext,
):
    qr_code = await state.get_value("qr_code")
    amount = await state.get_value("amount")
    user = await db.user_service.get_user_by_telegram_id(c.from_user.id)
    establishment = await db.establishment_service.get_establishment_by_qr(qr_code)

    bill =  f"🧾 Оплата от {user.first_name} (ID: {user.id})\n" \
            f"Сумма: {amount} сум\n" \
            f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    await c.bot.send_message(
        chat_id=establishment.owner.telegram_id,
        text=bill
    )
    await c.message.edit_text("✅ Оплачено")
    await c.message.answer(
        text=bill
    )

    await db.user_service.withdraw_from_balance(
        telegram_id=c.from_user.id,
        establishment_id=establishment.id,
        amount=amount
    )


