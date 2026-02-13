from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.callbacks.ticket_cb import TicketViewCB, MasterActionCB, CarPlateApprovalCB
from bot.callbacks.navigation_cb import PageCB, MasterMenuCB, MenuCB
from bot.utils.constants import CATEGORY_DISPLAY, TicketCategory


def master_main_menu() -> InlineKeyboardMarkup:
    from bot.services.text_service import get_text_sync
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text_sync("btn_new_tickets"), callback_data=MasterMenuCB(action="new").pack())],
        [InlineKeyboardButton(text=get_text_sync("btn_active_tickets"), callback_data=MasterMenuCB(action="active").pack())],
        [InlineKeyboardButton(text=get_text_sync("btn_completed"), callback_data=MasterMenuCB(action="completed").pack())],
        [InlineKeyboardButton(text="Тіл / Язык", callback_data=MasterMenuCB(action="change_lang").pack())],
    ])


def master_ticket_actions(ticket_pk: int, status: str) -> InlineKeyboardMarkup:
    buttons = []

    # Car plate approval - show approve/reject buttons
    if status == "pending_approval":
        buttons.append([
            InlineKeyboardButton(
                text="✅ Одобрить",
                callback_data=CarPlateApprovalCB(ticket_pk=ticket_pk, action="approve").pack(),
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=CarPlateApprovalCB(ticket_pk=ticket_pk, action="reject").pack(),
            ),
        ])
    # Regular tickets - show accept/complete buttons
    elif status == "new":
        buttons.append([
            InlineKeyboardButton(
                text="Принять",
                callback_data=MasterActionCB(ticket_pk=ticket_pk, action="accept").pack(),
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text="Выполнена",
                callback_data=MasterActionCB(ticket_pk=ticket_pk, action="complete").pack(),
            )
        ])
    elif status == "in_progress":
        buttons.append([
            InlineKeyboardButton(
                text="Выполнена",
                callback_data=MasterActionCB(ticket_pk=ticket_pk, action="complete").pack(),
            )
        ])
    elif status in ("master_approved", "master_rejected"):
        # Waiting for admin decision - no action buttons, just info
        pass

    buttons.append([InlineKeyboardButton(text="Назад", callback_data=MenuCB(action="master").pack())])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def master_ticket_list(tickets: list, page: int, total_pages: int, scope: str) -> InlineKeyboardMarkup:
    buttons = []
    for t in tickets:
        # Show category in Russian
        try:
            cat_display = CATEGORY_DISPLAY.get(TicketCategory(t.category), t.category)
        except ValueError:
            cat_display = t.category
        buttons.append([
            InlineKeyboardButton(
                text=f"№{t.ticket_id} — {cat_display}",
                callback_data=TicketViewCB(ticket_pk=t.id).pack(),
            )
        ])
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(
            text="◀ Назад",
            callback_data=PageCB(scope=scope, page=page - 1).pack(),
        ))
    if page < total_pages:
        nav.append(InlineKeyboardButton(
            text="Вперед ▶",
            callback_data=PageCB(scope=scope, page=page + 1).pack(),
        ))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="Меню мастера", callback_data=MenuCB(action="master").pack())])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
