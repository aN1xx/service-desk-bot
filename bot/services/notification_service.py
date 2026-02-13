import logging
from contextlib import contextmanager

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks.ticket_cb import TicketRateCB, MasterActionCB, CarPlateApprovalCB
from bot.db.repositories import admin_repo
from bot.services.text_service import get_text_sync
from bot.utils.constants import STATUS_DISPLAY
from bot.utils.language import current_language, DEFAULT_LANGUAGE

logger = logging.getLogger(__name__)


@contextmanager
def _with_lang(lang: str):
    """Temporarily set current_language for get_text_sync calls."""
    token = current_language.set(lang or DEFAULT_LANGUAGE)
    try:
        yield
    finally:
        current_language.reset(token)


async def _safe_send(bot: Bot, chat_id: int, text: str, **kwargs) -> bool:
    try:
        await bot.send_message(chat_id, text, **kwargs)
        return True
    except Exception as e:
        logger.warning("Failed to send message to %s: %s", chat_id, e)
        return False


async def _safe_send_photo(bot: Bot, chat_id: int, photo: str, caption: str = None, **kwargs) -> bool:
    """Send a photo with optional caption."""
    try:
        await bot.send_photo(chat_id, photo, caption=caption, **kwargs)
        return True
    except Exception as e:
        logger.warning("Failed to send photo to %s: %s", chat_id, e)
        return False


async def _safe_send_document(bot: Bot, chat_id: int, document: str, caption: str = None, **kwargs) -> bool:
    """Send a document with optional caption."""
    try:
        await bot.send_document(chat_id, document, caption=caption, **kwargs)
        return True
    except Exception as e:
        logger.warning("Failed to send document to %s: %s", chat_id, e)
        return False


async def notify_owner_ticket_created(
    bot: Bot, owner_telegram_id: int, ticket_id: str, recipient_lang: str = "ru",
) -> None:
    with _with_lang(recipient_lang):
        text = get_text_sync("create_submitted", ticket_id=ticket_id)
    await _safe_send(bot, owner_telegram_id, text)


async def notify_owner_status_changed(
    bot: Bot, owner_telegram_id: int, ticket_id: str, new_status: str,
    master_name: str | None = None, recipient_lang: str = "ru",
) -> None:
    with _with_lang(recipient_lang):
        status_text = STATUS_DISPLAY.get(new_status, new_status)
        if new_status == "in_progress" and master_name:
            text = get_text_sync("notify_status_with_master", ticket_id=ticket_id, status=status_text, master=master_name)
        else:
            text = get_text_sync("notify_status_changed", ticket_id=ticket_id, status=status_text)
    await _safe_send(bot, owner_telegram_id, text)


async def notify_owner_completed(
    bot: Bot, owner_telegram_id: int, ticket_id: str, ticket_pk: int,
    recipient_lang: str = "ru",
) -> None:
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"{i}⭐",
                callback_data=TicketRateCB(ticket_pk=ticket_pk, stars=i).pack(),
            )
            for i in range(1, 6)
        ]
    ])
    with _with_lang(recipient_lang):
        text = get_text_sync("notify_completed", ticket_id=ticket_id)
    await _safe_send(bot, owner_telegram_id, text, reply_markup=keyboard)


async def notify_master_new_ticket(
    bot: Bot, master_telegram_id: int, ticket_card: str, ticket_pk: int,
    recipient_lang: str = "ru",
) -> None:
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Принять",
                callback_data=MasterActionCB(ticket_pk=ticket_pk, action="accept").pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text="Выполнена",
                callback_data=MasterActionCB(ticket_pk=ticket_pk, action="complete").pack(),
            ),
        ],
    ])
    await _safe_send(bot, master_telegram_id, ticket_card, reply_markup=keyboard)


async def notify_admins_new_ticket(
    bot: Bot, session: AsyncSession, ticket_card: str
) -> None:
    admins = await admin_repo.get_all(session)
    for admin in admins:
        with _with_lang(getattr(admin, "language", "ru")):
            text = get_text_sync("notify_admin_new_ticket", card=ticket_card)
        await _safe_send(bot, admin.telegram_id, text)


async def notify_master_car_plate_approval(
    bot: Bot, master_telegram_id: int, ticket_card: str, ticket_pk: int,
    contract_photo: str | None = None, recipient_lang: str = "ru",
) -> None:
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Одобрить",
                callback_data=CarPlateApprovalCB(ticket_pk=ticket_pk, action="approve").pack(),
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=CarPlateApprovalCB(ticket_pk=ticket_pk, action="reject").pack(),
            ),
        ],
    ])
    with _with_lang(recipient_lang):
        text = get_text_sync("notify_car_plate_approval", card=ticket_card)

    # Send contract photo first if available
    if contract_photo:
        await _safe_send_photo(bot, master_telegram_id, contract_photo, caption="📎 Договор паркинга")

    await _safe_send(bot, master_telegram_id, text, reply_markup=keyboard)


async def notify_admin_car_plate_review(
    bot: Bot, session: AsyncSession, ticket_card: str, ticket_pk: int, master_decision: str,
    contract_photo: str | None = None
) -> None:
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Финально одобрить",
                callback_data=CarPlateApprovalCB(ticket_pk=ticket_pk, action="admin_approve").pack(),
            ),
            InlineKeyboardButton(
                text="❌ Финально отклонить",
                callback_data=CarPlateApprovalCB(ticket_pk=ticket_pk, action="admin_reject").pack(),
            ),
        ],
    ])
    admins = await admin_repo.get_all(session)
    for admin in admins:
        with _with_lang(getattr(admin, "language", "ru")):
            decision_text = "Одобрил" if master_decision == "approve" else "Отклонил"
            text = get_text_sync("notify_car_plate_admin_review", decision=decision_text, card=ticket_card)
        # Send contract photo first if available
        if contract_photo:
            await _safe_send_photo(bot, admin.telegram_id, contract_photo, caption="📎 Договор паркинга")
        await _safe_send(bot, admin.telegram_id, text, reply_markup=keyboard)


async def notify_owner_car_plate_decision(
    bot: Bot, owner_telegram_id: int, ticket_id: str, approved: bool,
    recipient_lang: str = "ru",
) -> None:
    with _with_lang(recipient_lang):
        if approved:
            text = get_text_sync("notify_car_plate_approved", ticket_id=ticket_id)
        else:
            text = get_text_sync("notify_car_plate_rejected", ticket_id=ticket_id)
    await _safe_send(bot, owner_telegram_id, text)


async def notify_master_car_plate_in_progress(
    bot: Bot, master_telegram_id: int, ticket_card: str, ticket_pk: int,
    recipient_lang: str = "ru",
) -> None:
    """Notify master that admin approved car plate and ticket is now in progress."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Выполнена",
                callback_data=MasterActionCB(ticket_pk=ticket_pk, action="complete").pack(),
            ),
        ],
    ])
    with _with_lang(recipient_lang):
        text = get_text_sync("notify_car_plate_in_progress", card=ticket_card)
    await _safe_send(bot, master_telegram_id, text, reply_markup=keyboard)
