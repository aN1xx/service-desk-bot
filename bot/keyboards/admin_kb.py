from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.callbacks.admin_cb import AdminFilterCB, AdminTicketCB, AdminReassignCB
from bot.callbacks.navigation_cb import PageCB, AdminMenuCB, MenuCB
from bot.utils.constants import (
    ResidentialComplex, COMPLEX_DISPLAY, STATUS_DISPLAY, TicketStatus,
)


def admin_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Все заявки", callback_data=AdminMenuCB(action="all").pack())],
        [
            InlineKeyboardButton(text="Новые", callback_data=AdminFilterCB(filter_type="status", value="new").pack()),
            InlineKeyboardButton(text="В работе", callback_data=AdminFilterCB(filter_type="status", value="in_progress").pack()),
        ],
        [
            InlineKeyboardButton(text="Выполнены (без оценки)", callback_data=AdminFilterCB(filter_type="status", value="completed").pack()),
            InlineKeyboardButton(text="Закрытые", callback_data=AdminFilterCB(filter_type="status", value="closed").pack()),
        ],
        [InlineKeyboardButton(text="Фильтр по ЖК", callback_data=AdminMenuCB(action="filter_complex").pack())],
        [InlineKeyboardButton(text="Фильтр по мастеру", callback_data=AdminMenuCB(action="filter_master").pack())],
        [InlineKeyboardButton(text="Фильтр по дате", callback_data=AdminMenuCB(action="filter_date").pack())],
        [InlineKeyboardButton(text="Тіл / Язык", callback_data=AdminMenuCB(action="change_lang").pack())],
    ])


def complex_filter_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for rc in ResidentialComplex:
        buttons.append([
            InlineKeyboardButton(
                text=COMPLEX_DISPLAY[rc],
                callback_data=AdminFilterCB(filter_type="complex", value=rc.value).pack(),
            )
        ])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data=MenuCB(action="admin").pack())])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def master_filter_keyboard(masters: list) -> InlineKeyboardMarkup:
    buttons = []
    for m in masters:
        buttons.append([
            InlineKeyboardButton(
                text=f"{m.full_name}",
                callback_data=AdminFilterCB(filter_type="master", value=str(m.id)).pack(),
            )
        ])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data=MenuCB(action="admin").pack())])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def date_filter_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сегодня", callback_data=AdminFilterCB(filter_type="date", value="today").pack())],
        [InlineKeyboardButton(text="Неделя", callback_data=AdminFilterCB(filter_type="date", value="week").pack())],
        [InlineKeyboardButton(text="Месяц", callback_data=AdminFilterCB(filter_type="date", value="month").pack())],
        [InlineKeyboardButton(text="Назад", callback_data=MenuCB(action="admin").pack())],
    ])


def admin_ticket_list(tickets: list, page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    for t in tickets:
        status_txt = STATUS_DISPLAY.get(t.status, t.status)
        buttons.append([
            InlineKeyboardButton(
                text=f"№{t.ticket_id} [{status_txt}]",
                callback_data=AdminTicketCB(action="view", ticket_pk=t.id).pack(),
            )
        ])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(
            text="◀ Назад",
            callback_data=PageCB(scope="admin_tickets", page=page - 1).pack(),
        ))
    if page < total_pages:
        nav.append(InlineKeyboardButton(
            text="Вперед ▶",
            callback_data=PageCB(scope="admin_tickets", page=page + 1).pack(),
        ))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="Меню админа", callback_data=MenuCB(action="admin").pack())])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_ticket_detail_kb(ticket_pk: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="История статусов",
            callback_data=AdminTicketCB(action="history", ticket_pk=ticket_pk).pack(),
        )],
        [InlineKeyboardButton(
            text="Сменить мастера",
            callback_data=AdminTicketCB(action="reassign", ticket_pk=ticket_pk).pack(),
        )],
        [InlineKeyboardButton(text="Назад к списку", callback_data=AdminMenuCB(action="all").pack())],
        [InlineKeyboardButton(text="Меню админа", callback_data=MenuCB(action="admin").pack())],
    ])


def reassign_master_keyboard(ticket_pk: int, masters: list) -> InlineKeyboardMarkup:
    buttons = []
    for m in masters:
        buttons.append([
            InlineKeyboardButton(
                text=f"{m.full_name} ({m.residential_complex})",
                callback_data=AdminReassignCB(ticket_pk=ticket_pk, master_id=m.id).pack(),
            )
        ])
    buttons.append([InlineKeyboardButton(text="Отмена", callback_data=MenuCB(action="admin").pack())])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
