import logging

from aiogram import Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin import admin_router as router
from bot.callbacks.admin_cb import AdminTicketCB
from bot.callbacks.ticket_cb import CarPlateApprovalCB
from bot.keyboards.admin_kb import admin_ticket_detail_kb, admin_main_menu
from bot.db.repositories import ticket_repo, owner_repo
from bot.utils.attachments import send_ticket_attachments
from bot.utils.formatting import format_ticket_card, format_history
from bot.utils.language import get_user_language
from bot.services.ticket_service import change_status
from bot.services.text_service import get_text
from bot.services.notification_service import notify_owner_car_plate_decision, notify_master_car_plate_in_progress

logger = logging.getLogger(__name__)


@router.callback_query(AdminTicketCB.filter())
async def admin_ticket_action(
    callback: CallbackQuery,
    callback_data: AdminTicketCB,
    session: AsyncSession,
    bot: Bot,
    **kwargs,
):
    action = callback_data.action
    ticket_pk = callback_data.ticket_pk

    ticket = await ticket_repo.get_by_id(session, ticket_pk)
    if not ticket:
        text = await get_text(session, "error_not_found")
        await callback.answer(text, show_alert=True)
        return

    if action == "view":
        # Send attachments first
        await send_ticket_attachments(bot, callback.from_user.id, ticket)

        text = format_ticket_card(ticket, include_client=True)
        try:
            await callback.message.edit_text(text, reply_markup=admin_ticket_detail_kb(ticket_pk))
        except Exception as e:
            logger.debug("edit_text failed (likely MessageNotModified): %s", e)

    elif action == "history":
        entries = await ticket_repo.get_history(session, ticket_pk)
        text = format_history(entries)
        btn_back = await get_text(session, "btn_back_to_ticket")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=btn_back,
                callback_data=AdminTicketCB(action="view", ticket_pk=ticket_pk).pack(),
            )],
        ])
        await callback.message.edit_text(text, reply_markup=kb)

    elif action == "reassign":
        from bot.db.repositories import master_repo
        from bot.keyboards.admin_kb import reassign_master_keyboard

        masters = await master_repo.get_all_active(session)
        if not masters:
            text = await get_text(session, "admin_no_masters")
            await callback.answer(text, show_alert=True)
            return
        text = await get_text(session, "admin_choose_master_for", ticket_id=ticket.ticket_id)
        await callback.message.edit_text(text, reply_markup=reassign_master_keyboard(ticket_pk, masters))

    await callback.answer()


@router.callback_query(CarPlateApprovalCB.filter())
async def handle_admin_car_plate_decision(
    callback: CallbackQuery,
    callback_data: CarPlateApprovalCB,
    session: AsyncSession,
    bot: Bot,
    **kwargs,
):
    action = callback_data.action

    if action not in ("admin_approve", "admin_reject"):
        return

    ticket = await ticket_repo.get_by_id(session, callback_data.ticket_pk)
    if not ticket:
        text = await get_text(session, "error_not_found")
        await callback.answer(text, show_alert=True)
        return

    if ticket.status not in ("master_approved", "master_rejected", "pending_approval"):
        text = await get_text(session, "master_already_reviewed")
        await callback.answer(text, show_alert=True)
        return

    if action == "admin_approve":
        # Find the master who approved this ticket
        from bot.db.repositories import master_repo

        approving_master_tg_id = await ticket_repo.get_approving_master_id(session, ticket.id)
        master = None
        if approving_master_tg_id:
            master = await master_repo.get_by_telegram_id(session, approving_master_tg_id)

        # Change status to in_progress (not just approved) so master can finalize
        await change_status(
            session,
            ticket_pk=ticket.id,
            old_status=ticket.status,
            new_status="in_progress",
            changed_by_id=callback.from_user.id,
            changed_by_role="admin",
            comment="Администратор одобрил заявку на госномер, передано мастеру для добавления в систему",
        )

        # Assign ticket to the approving master
        if master:
            await ticket_repo.reassign_master(session, ticket.id, master.id)

        await session.commit()

        # Notify owner about approval
        owner = await owner_repo.get_by_telegram_id(session, ticket.client_telegram_id)
        owner_lang = get_user_language(owner)
        await notify_owner_car_plate_decision(bot, ticket.client_telegram_id, ticket.ticket_id, True, recipient_lang=owner_lang)

        # Notify master that ticket is now in progress for them to add car plate
        if master:
            from bot.utils.formatting import format_ticket_card
            card = format_ticket_card(ticket)
            master_lang = get_user_language(master)
            await notify_master_car_plate_in_progress(bot, master.telegram_id, card, ticket.id, recipient_lang=master_lang)

        text = await get_text(session, "admin_car_plate_approved", ticket_id=ticket.ticket_id)
        await callback.message.edit_text(text, reply_markup=admin_main_menu())
        toast = await get_text(session, "toast_ticket_approved")
        await callback.answer(toast)

    elif action == "admin_reject":
        await change_status(
            session,
            ticket_pk=ticket.id,
            old_status=ticket.status,
            new_status="rejected",
            changed_by_id=callback.from_user.id,
            changed_by_role="admin",
            comment="Администратор отклонил заявку на госномер",
        )
        await session.commit()

        owner = await owner_repo.get_by_telegram_id(session, ticket.client_telegram_id)
        owner_lang = get_user_language(owner)
        await notify_owner_car_plate_decision(bot, ticket.client_telegram_id, ticket.ticket_id, False, recipient_lang=owner_lang)

        text = await get_text(session, "admin_car_plate_rejected", ticket_id=ticket.ticket_id)
        await callback.message.edit_text(text, reply_markup=admin_main_menu())
        toast = await get_text(session, "toast_ticket_rejected")
        await callback.answer(toast)
