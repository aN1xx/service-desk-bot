from aiogram.filters.callback_data import CallbackData


class AdminFilterCB(CallbackData, prefix="af"):
    filter_type: str  # status, complex, master
    value: str


class AdminTicketCB(CallbackData, prefix="at"):
    action: str  # view, history, reassign
    ticket_pk: int


class AdminReassignCB(CallbackData, prefix="ar"):
    ticket_pk: int
    master_id: int
