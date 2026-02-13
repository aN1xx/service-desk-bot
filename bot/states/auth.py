from aiogram.fsm.state import State, StatesGroup


class AuthState(StatesGroup):
    choosing_language = State()
    waiting_contact = State()
