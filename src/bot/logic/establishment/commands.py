from aiogram import F, types
from aiogram.fsm.context import FSMContext

from src.bot.structures.fsm.establishment import ProcessEstablishment
from src.services.tg_bot_service import TelegramBotService
from src.bot.structures.keyboards import common

from .router import establishment_router
from datetime import datetime, timedelta
from pathlib import Path


@establishment_router.message(F.text == "⬅️ Orqaga")
async def go_back(
    message: types.Message,
    state: FSMContext,
):
    await state.clear()
    await message.answer(
        "Assalomu aleykum",
        reply_markup=common.establishment_menu()
    )
    await state.set_state(ProcessEstablishment.select_menu)


@establishment_router.message(ProcessEstablishment.select_menu, F.text == "Tranzaksiyalar")
async def get_transactions(
    message: types.Message,
    db: TelegramBotService,
    state: FSMContext,
):
    await message.answer("Filterni tanlang", reply_markup=common.establishment_filters())
    await state.set_state(ProcessEstablishment.select_type)


@establishment_router.message(ProcessEstablishment.select_type, F.text == "Sana bo'yicha")
async def by_date(
    message: types.Message,
    db: TelegramBotService,
    state: FSMContext,
):
    await message.answer(
        "Sanani shunday formatda yuboring:\n\n<code>01.01.2025-01.06.2025</code>\n\nYoki quyidagilardan birini tanlang:",
        reply_markup=common.date_filters()
    )
    await state.set_state(ProcessEstablishment.send_date_filter)


@establishment_router.message(ProcessEstablishment.send_date_filter, F.text == "Kunlik")
async def by_daily(
    message: types.Message,
    db: TelegramBotService,
    state: FSMContext,
):
    establishment_transactions = await db.establishment_service.get_establishment_transactions(
        establishment_owner_telegram_id=message.from_user.id,
        start_date=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
        end_date=datetime.now(),
    )
    if not establishment_transactions:
        return await message.answer("Bugun uchun tranzaksiyalar topilmadi.")
    else:
        transactions_message = "Tranzaktsiyalar:\n\n"
        transactions_message += f"Muassasa: {establishment_transactions[0].establishment.name}\n\n"
        for transaction in establishment_transactions:
            transactions_message += (
                f"ID: {transaction.id}\n"
                f"Summa: {transaction.amount} сум\n"
                f"Mijoz: {transaction.user.first_name}\n"
                f"Vaqt: {transaction.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
        await message.answer(transactions_message)


@establishment_router.message(ProcessEstablishment.send_date_filter, F.text == "Haftalik")
async def by_weekly(
    message: types.Message,
    db: TelegramBotService,
    state: FSMContext,
):
    establishment_transactions = await db.establishment_service.get_establishment_transactions(
        establishment_owner_telegram_id=message.from_user.id,
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now(),
    )
    if not establishment_transactions:
        return await message.answer("Oxirgi 7 kun uchun tranzaksiyalar topilmadi.")
    else:
        transactions_message = "Tranzaktsiyalar:\n\n"
        for transaction in establishment_transactions:
            transactions_message += (
                f"ID: {transaction.id}\n"
                f"Summa: {transaction.amount} сум\n"
                f"Muassasa: {transaction.establishment.name}\n"
                f"Vaqt: {transaction.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
        await message.answer(transactions_message)


@establishment_router.message(ProcessEstablishment.send_date_filter, F.text == "Oylik")
async def by_monthly(
    message: types.Message,
    db: TelegramBotService,
    state: FSMContext,
):
    establishment_transactions = await db.establishment_service.get_establishment_transactions(
        establishment_owner_telegram_id=message.from_user.id,
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now(),
    )
    if not establishment_transactions:
        return await message.answer("Oxirgi 30 kun uchun tranzaksiyalar topilmadi.")
    else:
        transactions_message = "Tranzaktsiyalar:\n\n"
        for transaction in establishment_transactions:
            transactions_message += (
                f"ID: {transaction.id}\n"
                f"Summa: {transaction.amount} сум\n"
                f"Muassasa: {transaction.establishment.name}\n"
                f"Vaqt: {transaction.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
        await message.answer(transactions_message)


@establishment_router.message(ProcessEstablishment.send_date_filter, F.text)
async def by_data(
    message: types.Message,
    db: TelegramBotService,
    state: FSMContext,
):
    dates = message.text.split("-")
    if len(dates) != 2:
        return await message.answer("Sanani to'g'ri formatda kiriting:\n\n<code>01.01.2025-01.06.2025</code>")

    try:
        start_date = datetime.strptime(dates[0].strip(), "%d.%m.%Y")
        end_date = datetime.strptime(dates[1].strip(), "%d.%m.%Y")
        if start_date > end_date:
            return await message.answer("Boshlanish sanasi tugash sanasidan katta bo'lmasligi kerak.")

        establishment_transactions = await db.establishment_service.get_establishment_transactions(
            establishment_owner_telegram_id=message.from_user.id,
            start_date=start_date,
            end_date=end_date,
        )
        if not establishment_transactions:
            return await message.answer("Bu sanalar orasida tranzaksiyalar topilmadi.")
        else:
            transactions_message = "Tranzaktsiyalar:\n\n"
            for transaction in establishment_transactions:
                transactions_message += (
                    f"ID: {transaction.id}\n"
                    f"Summa: {transaction.amount} сум\n"
                    f"Muassasa: {transaction.establishment.name}\n"
                    f"Vaqt: {transaction.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                )
            await message.answer(transactions_message)
    except ValueError:
        return await message.answer("Sanani to'g'ri formatda kiriting:\n\n<code>01.01.2025-01.06.2025</code>")


@establishment_router.message(ProcessEstablishment.select_type, F.text == "Mijoz IDsi bo'yicha")
async def start_handler(
    message: types.Message,
    db: TelegramBotService,
    state: FSMContext,
):
    await message.answer("Mijos IDsini jo'nating")
    await state.set_state(ProcessEstablishment.send_id_filter)


@establishment_router.message(ProcessEstablishment.send_id_filter, F.text)
async def start_handler(
    message: types.Message,
    db: TelegramBotService,
    state: FSMContext,
):
    if not message.text.isdigit():
        return await message.answer("Iltimos, to'g'ri ID kiriting.")

    user_transactions = await db.transaction_service.get_transactions_by_user_and_establishment(
        user_id=int(message.text),
        establishment_owner_telegram_id=message.from_user.id
    )
    if not user_transactions:
        return await message.answer("Bu mijoz uchun tranzaksiyalar topilmadi.")
    else:
        transactions_message = "Tranzaktsiyalar:\n\n"
        for transaction in user_transactions:
            transactions_message += (
                f"ID: {transaction.id}\n"
                f"Summa: {transaction.amount} сум\n"
                f"Muassasa: {transaction.establishment.name}\n"
                f"Vaqt: {transaction.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
        await message.answer(transactions_message)


@establishment_router.message(F.text == "Umumiy daromad")
async def establishment_total_profit(
    message: types.Message,
    db: TelegramBotService,
    state: FSMContext
):
    establishment = await db.establishment_service.get_establishment_by_owner_telegram_id(
        owner_telegram_id=message.from_user.id
    )
    total_revenue = await db.establishment_service.get_establishment_total_revenue(
        establishment_id=establishment.id
    )
    await message.answer(
        f"Umumiy daromad: {total_revenue}"
    )


@establishment_router.message(F.text == "Hisobotni olish PDF/Excel")
async def establishment_total_profit(
    message: types.Message,
    db: TelegramBotService,
    state: FSMContext
):
    await message.answer(
        "File turini tanlang", reply_markup=common.choose_file_type()
    )


@establishment_router.message(F.text == "PDF")
async def send_report_pdf(
    message: types.Message,
    db: TelegramBotService,
    state: FSMContext
):
    establishment = await db.establishment_service.get_establishment_by_owner_telegram_id(
        owner_telegram_id=message.from_user.id
    )
    result = await db.establishment_service.get_revenue_summary_in_pdf(establishment.id)

    # result is a relative path like 'reports/filename.pdf'

    file_path = Path(result).resolve()
    if not file_path.exists():
        return await message.answer("PDF faylini topib bo'lmadi.")

    with file_path.open("rb") as pdf_file:
        await message.answer_document(
            types.BufferedInputFile(pdf_file.read(), filename=file_path.name),
            caption="Hisobot PDF fayli"
        )


@establishment_router.message(F.text == "EXCEL")
async def send_report_excel(
    message: types.Message,
    db: TelegramBotService,
    state: FSMContext
):
    establishment = await db.establishment_service.get_establishment_by_owner_telegram_id(
        owner_telegram_id=message.from_user.id
    )
    result = await db.establishment_service.get_revenue_summary_in_excel(establishment.id)

    # result is a relative path like 'reports/filename.xlsx'

    file_path = Path(result).resolve()
    if not file_path.exists():
        return await message.answer("XLSX faylini topib bo'lmadi.")

    with file_path.open("rb") as xlsx_file:
        await message.answer_document(
            types.BufferedInputFile(xlsx_file.read(), filename=file_path.name),
            caption="Hisobot EXCEL fayli"
        )
