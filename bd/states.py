from aiogram.fsm.state import State, StatesGroup


class StatusAuth(StatesGroup):
    waiting_for_password = State()
