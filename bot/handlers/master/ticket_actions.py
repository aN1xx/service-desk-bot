import logging

from aiogram import Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.master import master_router as router
from bot.callbacks.ticket_cb import MasterActionCB, CarPlateApprovalCB
from bot.db.repositories import ticket_repo, owner_repo
from bot.services.ticket_service import change_status
from bot.utils.language import get_user_language
from bot.services.text_service import get_text
from bot.services.notification_service import (
    notify_owner_status_changed,
    notify_owner_completed,
    notify_admin_car_plate_review,
)
from bot.keyboards.master_kb import master_main_menu, master_ticket_actions
from bot.utils.formatting import format_ticket_card

logger = logging.getLogger(__name__)


@router.callback_query(MasterActionCB.filter())
async def handle_master_action(
    callback: CallbackQuery,
    callback_data: MasterActionCB,
    session: AsyncSession,
    bot: Bot,
    user_obj=None,
    **kwargs,
):
    ticket = await ticket_repo.get_by_id(session, callback_data.ticket_pk)
    if not ticket:
        text = await get_text(session, "error_not_found")
        await callback.answer(text, show_alert=True)
        return

    action = callback_data.action

    if action == "accept":
        if ticket.status not in ("new",):
            text = await get_text(session, "master_already_in_progress")
            await callback.answer(text, show_alert=True)
            return

        try:
            await change_status(
                session,
                ticket_pk=ticket.id,
                old_status=ticket.status,
                new_status="in_progress",
                changed_by_id=callback.from_user.id,
                changed_by_role="master",
                comment="Мастер принял заявку",
            )

            if not ticket.assigned_master_id and user_obj:
                await ticket_repo.reassign_master(session, ticket.id, user_obj.id)

            await session.commit()
        except Exception:
            logger.exception("Failed to accept ticket %s", ticket.ticket_id)
            text = await get_text(session, "error_generic")
            await callback.answer(text, show_alert=True)
            return

        master_name = user_obj.full_name if user_obj else "мастер"
        owner = await owner_repo.get_by_telegram_id(session, ticket.client_telegram_id)
        owner_lang = get_user_language(owner)
        await notify_owner_status_changed(
            bot, ticket.client_telegram_id, ticket.ticket_id,
            "in_progress", master_name=master_name, recipient_lang=owner_lang,
        )

        text = await get_text(session, "master_ticket_accepted", ticket_id=ticket.ticket_id)
        await callback.message.edit_text(text, reply_markup=master_main_menu())
        toast = await get_text(session, "toast_ticket_accepted")
        await callback.answer(toast)

    elif action == "complete":
        if ticket.status not in ("new", "in_progress"):
            text = await get_text(session, "master_cannot_complete")
            await callback.answer(text, show_alert=True)
            return

        try:
            await change_status(
                session,
                ticket_pk=ticket.id,
                old_status=ticket.status,
                new_status="completed",
                changed_by_id=callback.from_user.id,
                changed_by_role="master",
                comment="Мастер выполнил заявку",
            )
            await session.commit()
        except Exception:
            logger.exception("Failed to complete ticket %s", ticket.ticket_id)
            text = await get_text(session, "error_generic")
            await callback.answer(text, show_alert=True)
            return

        owner = await owner_repo.get_by_telegram_id(session, ticket.client_telegram_id)
        owner_lang = get_user_language(owner)
        await notify_owner_completed(
            bot, ticket.client_telegram_id, ticket.ticket_id, ticket.id,
            recipient_lang=owner_lang,
        )

        text = await get_text(session, "master_ticket_completed", ticket_id=ticket.ticket_id)
        await callback.message.edit_text(text, reply_markup=master_main_menu())
        toast = await get_text(session, "toast_ticket_completed")
        await callback.answer(toast)

    else:
        logger.warning("Unknown master action: %s for ticket %s", action, callback_data.ticket_pk)


@router.callback_query(CarPlateApprovalCB.filter())
async def handle_car_plate_approval(
    callback: CallbackQuery,
    callback_data: CarPlateApprovalCB,
    session: AsyncSession,
    bot: Bot,
    user_obj=None,
    **kwargs,
):
    ticket = await ticket_repo.get_by_id(session, callback_data.ticket_pk)
    if not ticket:
        text = await get_text(session, "error_not_found")
        await callback.answer(text, show_alert=True)
        return

    action = callback_data.action

    if action not in ("approve", "reject"):
        return

    if ticket.status != "pending_approval":
        text = await get_text(session, "master_already_reviewed")
        await callback.answer(text, show_alert=True)
        return

    if action == "approve":
        await change_status(
            session,
            ticket_pk=ticket.id,
            old_status=ticket.status,
            new_status="master_approved",
            changed_by_id=callback.from_user.id,
            changed_by_role="master",
            comment="Мастер одобрил заявку на госномер",
        )

        # Assign ticket to this master so it appears in their active list
        if user_obj:
            await ticket_repo.reassign_master(session, ticket.id, user_obj.id)

        await session.commit()

        card = format_ticket_card(ticket)
        contract_photo = getattr(ticket, "parking_contract_photo", None)
        await notify_admin_car_plate_review(bot, session, card, ticket.id, "approve", contract_photo=contract_photo)

        text = await get_text(session, "master_car_plate_approved", ticket_id=ticket.ticket_id)
        await callback.message.edit_text(text, reply_markup=master_main_menu())
        toast = await get_text(session, "toast_ticket_approved")
        await callback.answer(toast)

    elif action == "reject":
        await change_status(
            session,
            ticket_pk=ticket.id,
            old_status=ticket.status,
            new_status="master_rejected",
            changed_by_id=callback.from_user.id,
            changed_by_role="master",
            comment="Мастер отклонил заявку на госномер",
        )
        await session.commit()

        card = format_ticket_card(ticket)
        contract_photo = getattr(ticket, "parking_contract_photo", None)
        await notify_admin_car_plate_review(bot, session, card, ticket.id, "reject", contract_photo=contract_photo)

        text = await get_text(session, "master_car_plate_rejected", ticket_id=ticket.ticket_id)
        await callback.message.edit_text(text, reply_markup=master_main_menu())
        toast = await get_text(session, "toast_ticket_rejected")
        await callback.answer(toast)
