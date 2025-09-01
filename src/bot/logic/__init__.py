"""This package is used for a bot logic implementation."""

from .admin import admin_router
from .help import help_router
from .start import start_router
from .user import user_router
from .establishment import establishment_router

routers = (
    start_router,
    help_router,
    admin_router,
    user_router,
    establishment_router,
)
