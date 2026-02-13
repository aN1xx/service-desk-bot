import logging

from aiogram import Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin import admin_router as router
from bot.callbacks.admin_cb import AdminReassignCB
from bot.db.repositories import ticket_repo, master_repo
from bot.keyboards.admin_kb import admin_main_menu
from bot.services.notification_service import notify_master_new_ticket
from bot.services.text_service import get_text
from bot.utils.formatting import format_ticket_card

logger = logging.getLogger(__name__)


@router.callback_query(AdminReassignCB.filter())
async def reassign_master(
    callback: CallbackQuery,
    callback_data: AdminReassignCB,
    session: AsyncSession,
    bot: Bot,
    **kwargs,
):
    ticket = await ticket_repo.get_by_id(session, callback_data.ticket_pk)
    if not ticket:
        text = await get_text(session, "error_not_found")
        await callback.answer(text, show_alert=True)
        return

    master = await master_repo.get_by_id(session, callback_data.master_id)
    if not master:
        text = await get_text(session, "admin_master_not_found")
        await callback.answer(text, show_alert=True)
        return

    try:
        await ticket_repo.reassign_master(session, ticket.id, master.id)
        await ticket_repo.add_history(
            session,
            ticket_pk=ticket.id,
            old_status=ticket.status,
            new_status=ticket.status,
            changed_by_id=callback.from_user.id,
            changed_by_role="admin",
            comment=f"Мастер изменен на: {master.full_name}",
        )
        await session.commit()
    except Exception:
        logger.exception("Failed to reassign ticket %s", ticket.ticket_id)
        text = await get_text(session, "error_generic")
        await callback.answer(text, show_alert=True)
        return

    card = format_ticket_card(ticket)
    from bot.utils.language import get_user_language
    await notify_master_new_ticket(bot, master.telegram_id, card, ticket.id, recipient_lang=get_user_language(master))

    text = await get_text(session, "admin_master_reassigned", ticket_id=ticket.ticket_id, master_name=master.full_name)
    await callback.message.edit_text(text, reply_markup=admin_main_menu())
    text = await get_text(session, "admin_master_assigned")
    await callback.answer(text)
    logger.info("Ticket %s reassigned to master %s by admin %s", ticket.ticket_id, master.id, callback.from_user.id)
