from aiogram.fsm.state import State, StatesGroup


class RateTicketState(StatesGroup):
    waiting_comment = State()
