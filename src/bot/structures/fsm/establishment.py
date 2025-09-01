from aiogram.fsm.state import State, StatesGroup


class ProcessEstablishment(StatesGroup):
    """Use this state for registration."""

    select_menu = State()
    select_type = State()
    send_date_filter = State()
    send_id_filter = State()
