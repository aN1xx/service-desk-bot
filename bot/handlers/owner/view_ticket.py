import logging

from aiogram import Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.owner import owner_router as router
from bot.callbacks.navigation_cb import OwnerMenuCB, MenuCB
from bot.callbacks.ticket_cb import TicketViewCB
from bot.db.repositories import ticket_repo
from bot.utils.attachments import send_ticket_attachments
from bot.utils.formatting import format_ticket_card
from bot.services.text_service import get_text

logger = logging.getLogger(__name__)


@router.callback_query(TicketViewCB.filter())
async def view_ticket(callback: CallbackQuery, callback_data: TicketViewCB, session: AsyncSession, bot: Bot, **kwargs):
    ticket = await ticket_repo.get_by_id(session, callback_data.ticket_pk)
    if not ticket:
        text = await get_text(session, "error_not_found")
        await callback.answer(text, show_alert=True)
        return

    # Send all attachments first
    await send_ticket_attachments(bot, callback.from_user.id, ticket)

    text = format_ticket_card(ticket, include_client=False)
    btn_back = await get_text(session, "btn_back_to_tickets")
    btn_menu = await get_text(session, "btn_main_menu")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_back, callback_data=OwnerMenuCB(action="tickets").pack())],
        [InlineKeyboardButton(text=btn_menu, callback_data=MenuCB(action="owner").pack())],
    ])
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception as e:
        logger.debug("edit_text failed (likely MessageNotModified): %s", e)
    await callback.answer()
