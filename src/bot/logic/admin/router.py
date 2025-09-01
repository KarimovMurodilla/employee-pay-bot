from aiogram import Router

from src.bot.filters.admin_filter import AdminFilter

admin_router = Router(name="admin")
admin_router.message.filter(AdminFilter())
