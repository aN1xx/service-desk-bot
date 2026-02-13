from aiogram.fsm.state import State, StatesGroup


class AdminFilterState(StatesGroup):
    choosing_date_from = State()
    choosing_date_to = State()
