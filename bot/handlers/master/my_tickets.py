import logging

from aiogram import F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.master import master_router as router
from bot.callbacks.navigation_cb import PageCB, MasterMenuCB
from bot.callbacks.ticket_cb import TicketViewCB
from bot.keyboards.master_kb import master_ticket_list, master_main_menu, master_ticket_actions
from bot.db.repositories import ticket_repo
from bot.services.text_service import get_text
from bot.utils.attachments import send_ticket_attachments
from bot.utils.pagination import paginate
from bot.utils.constants import STATUS_DISPLAY
from bot.utils.formatting import format_ticket_card

logger = logging.getLogger(__name__)


@router.callback_query(MasterMenuCB.filter(F.action == "new"))
async def show_new_tickets(callback: CallbackQuery, session: AsyncSession, user_obj=None, **kwargs):
    await _show_new_tickets_by_complex(callback, session, user_obj)


@router.callback_query(MasterMenuCB.filter(F.action == "active"))
async def show_active_tickets(callback: CallbackQuery, session: AsyncSession, user_obj=None, **kwargs):
    # Show in_progress + master_approved (waiting for admin decision) + master_rejected
    await _show_master_tickets(callback, session, user_obj, scope="master_active", statuses=["in_progress", "master_approved", "master_rejected"])


@router.callback_query(MasterMenuCB.filter(F.action == "completed"))
async def show_completed_tickets(callback: CallbackQuery, session: AsyncSession, user_obj=None, **kwargs):
    # Show both "completed" and "closed" (rated) tickets
    await _show_master_tickets(callback, session, user_obj, statuses=["completed", "closed"], scope="master_completed")


@router.callback_query(PageCB.filter(F.scope.startswith("master_")))
async def paginate_master_tickets(callback: CallbackQuery, callback_data: PageCB, session: AsyncSession, user_obj=None, **kwargs):
    scope = callback_data.scope
    page = callback_data.page

    if scope == "master_new":
        await _show_new_tickets_by_complex(callback, session, user_obj, page=page)
        return

    if scope == "master_completed":
        # Show both "completed" and "closed" (rated) tickets
        await _show_master_tickets(callback, session, user_obj, statuses=["completed", "closed"], scope=scope, page=page)
        return

    if scope == "master_active":
        await _show_master_tickets(callback, session, user_obj, statuses=["in_progress", "master_approved", "master_rejected"], scope=scope, page=page)
        return

    await _show_master_tickets(callback, session, user_obj, status="in_progress", scope=scope, page=page)


def _parse_master_complexes(user_obj) -> list[str]:
    if not user_obj or not user_obj.residential_complex:
        return []
    return [c.strip() for c in user_obj.residential_complex.split(",") if c.strip()]


async def _show_new_tickets_by_complex(callback, session, user_obj, page=1):
    if not user_obj:
        text = await get_text(session, "error_auth")
        await callback.answer(text, show_alert=True)
        return

    complexes = _parse_master_complexes(user_obj)
    if not complexes:
        text = await get_text(session, "master_no_complexes")
        await callback.message.edit_text(text, reply_markup=master_main_menu())
        await callback.answer()
        return

    total = await ticket_repo.count_new_for_master(session, complexes)

    if total == 0:
        text = await get_text(session, "master_no_new")
        await callback.message.edit_text(text, reply_markup=master_main_menu())
        await callback.answer()
        return

    offset, limit, total_pages = paginate(total, page)
    tickets = await ticket_repo.list_new_for_master(session, complexes, limit=limit, offset=offset)

    text = await get_text(session, "master_new_tickets", page=page, total=total_pages)
    await callback.message.edit_text(text, reply_markup=master_ticket_list(tickets, page, total_pages, "master_new"))
    await callback.answer()


async def _show_master_tickets(callback, session, user_obj, scope, page=1, status=None, statuses=None):
    if not user_obj:
        text = await get_text(session, "error_auth")
        await callback.answer(text, show_alert=True)
        return

    total = await ticket_repo.count_by_master(session, user_obj.id, status=status, statuses=statuses)

    # Determine display name for the scope
    scope_display = {
        "master_active": "Активные",
        "master_completed": "Выполненные",
    }

    if total == 0:
        status_name = scope_display.get(scope) or STATUS_DISPLAY.get(status, status)
        text = await get_text(session, "master_no_tickets", status=status_name)
        await callback.message.edit_text(text, reply_markup=master_main_menu())
        await callback.answer()
        return

    offset, limit, total_pages = paginate(total, page)
    tickets = await ticket_repo.list_by_master(session, user_obj.id, status=status, statuses=statuses, limit=limit, offset=offset)

    status_name = scope_display.get(scope) or STATUS_DISPLAY.get(status, status)
    text = await get_text(session, "master_tickets_page", status=status_name, page=page, total=total_pages)
    await callback.message.edit_text(text, reply_markup=master_ticket_list(tickets, page, total_pages, scope))
    await callback.answer()


@router.callback_query(TicketViewCB.filter())
async def view_master_ticket(callback: CallbackQuery, callback_data: TicketViewCB, session: AsyncSession, bot: Bot, **kwargs):
    ticket_pk = callback_data.ticket_pk
    ticket = await ticket_repo.get_by_id(session, ticket_pk)
    if not ticket:
        text = await get_text(session, "error_not_found")
        await callback.answer(text, show_alert=True)
        return

    # Send all attachments first
    await send_ticket_attachments(bot, callback.from_user.id, ticket)

    text = format_ticket_card(ticket, include_client=True)
    try:
        await callback.message.edit_text(text, reply_markup=master_ticket_actions(ticket.id, ticket.status))
    except Exception as e:
        logger.debug("edit_text failed (likely MessageNotModified): %s", e)
    await callback.answer()
