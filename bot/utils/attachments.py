import logging

from aiogram import Bot

logger = logging.getLogger(__name__)


async def send_ticket_attachments(bot: Bot, chat_id: int, ticket) -> None:
    """Send all ticket attachments (photos, documents) to the user."""
    try:
        # Send parking contract photo
        if getattr(ticket, "parking_contract_photo", None):
            try:
                await bot.send_photo(chat_id, ticket.parking_contract_photo, caption="📎 Договор паркинга")
            except Exception:
                try:
                    await bot.send_document(chat_id, ticket.parking_contract_photo, caption="📎 Договор паркинга")
                except Exception as e:
                    logger.warning("Failed to send parking contract: %s", e)

        # Send face_id photos
        face_photos = getattr(ticket, "face_id_photos", None) or []
        for i, photo_id in enumerate(face_photos, 1):
            try:
                await bot.send_photo(chat_id, photo_id, caption=f"📷 Face ID фото {i}")
            except Exception as e:
                logger.warning("Failed to send face_id photo: %s", e)

        # Send general attachments
        attachments = getattr(ticket, "attachments", None) or []
        for i, file_id in enumerate(attachments, 1):
            try:
                await bot.send_photo(chat_id, file_id, caption=f"📷 Вложение {i}")
            except Exception:
                try:
                    await bot.send_document(chat_id, file_id, caption=f"📎 Вложение {i}")
                except Exception as e:
                    logger.warning("Failed to send attachment: %s", e)
    except Exception as e:
        logger.warning("Error sending attachments: %s", e)
