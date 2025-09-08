from aiogram.types import (
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def accept():
    builder = InlineKeyboardBuilder()

    # Add the "Back" button
    builder.row(
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="accept_purchase")
    )

    # Return the built keyboard
    return builder.as_markup()


def user_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Tranzaksiyalar")
    builder.button(text="Mening hisobim")
    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)


def establishment_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Tranzaksiyalar")
    builder.button(text="Umumiy daromad")
    builder.button(text="Hisobotni olish PDF/Excel")
    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)


def choose_file_type():
    builder = ReplyKeyboardBuilder()
    builder.button(text="PDF")
    builder.button(text="EXCEL")
    builder.button(text="⬅️ Orqaga")
    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)


def establishment_filters():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Sana bo'yicha")
    builder.button(text="Mijoz IDsi bo'yicha")
    builder.button(text="⬅️ Orqaga")
    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)


def date_filters():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Kunlik")
    builder.button(text="Haftalik")
    builder.button(text="Oylik")
    builder.button(text="⬅️ Orqaga")
    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)


# Просмотр глобальной статистики:
# • По компании.
# • По департаментам.
# • По каждому заведению.
# • ✅ Просмотр всех транзакций.
# • ✅ Просмотр расходов по каждому пользователю.(по отделам)
# • ✅ Проценты расходов по заведениям (доли).
# • ✅ Скачивание отчётов (PDF, Excel)


def admin_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Bo'limlar statistikasi")
    builder.button(text="Muassasalar statistikasi")
    builder.button(text="Barcha tranzaksiyalar")
    builder.button(text="Hisobotni olish PDF/Excel")
    builder.adjust(1)

    return builder.as_markup(resize_keyboard=True)
