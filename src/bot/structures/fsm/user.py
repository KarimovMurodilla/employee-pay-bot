from aiogram.fsm.state import State, StatesGroup


class ProcessUser(StatesGroup):
    """Use this state for registration."""

    select_menu = State()
    confirm_purchase = State()
    accept_purchase = State()
