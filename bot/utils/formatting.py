from bot.db.models.ticket import Ticket
from bot.db.models.ticket_history import TicketHistory
from bot.utils.constants import (
    COMPLEX_DISPLAY,
    CATEGORY_DISPLAY,
    STATUS_DISPLAY,
    ResidentialComplex,
    TicketCategory,
    TicketStatus,
)


def format_ticket_card(ticket: Ticket, include_client: bool = True) -> str:
    complex_name = COMPLEX_DISPLAY.get(ticket.residential_complex, ticket.residential_complex)
    category_name = CATEGORY_DISPLAY.get(ticket.category, ticket.category)
    status_name = STATUS_DISPLAY.get(ticket.status, ticket.status)

    lines = [
        f"<b>Заявка №{ticket.ticket_id}</b>",
        f"Статус: <b>{status_name}</b>",
        f"ЖК: {complex_name}",
        f"Категория: {category_name}",
    ]

    if ticket.sub_category:
        lines.append(f"Подкатегория: {ticket.sub_category}")

    address_parts = []
    if ticket.block:
        address_parts.append(f"блок {ticket.block}")
    if ticket.entrance:
        address_parts.append(f"подъезд {ticket.entrance}")
    if ticket.apartment:
        address_parts.append(f"кв. {ticket.apartment}")
    if address_parts:
        lines.append(f"Адрес: {', '.join(address_parts)}")

    if include_client:
        lines.append(f"Клиент: {ticket.client_full_name}")
        lines.append(f"Телефон: {ticket.client_phone}")

    lines.append(f"\nОписание: {ticket.description}")

    if ticket.car_plate:
        lines.append(f"Госномер: {ticket.car_plate}")
    if ticket.car_gate:
        lines.append(f"Заезд: {ticket.car_gate}")
    if hasattr(ticket, "has_parking") and ticket.has_parking is not None:
        lines.append(f"Есть паркинг: {'Да' if ticket.has_parking else 'Нет'}")
    if hasattr(ticket, "parking_reason") and ticket.parking_reason:
        lines.append(f"Причина: {ticket.parking_reason}")
    if hasattr(ticket, "parking_contract_photo") and ticket.parking_contract_photo:
        lines.append("📎 Договор паркинга: приложен")
    if ticket.parking_number:
        lines.append(f"Номер паркинга: {ticket.parking_number}")
    if ticket.camera_access_email:
        lines.append(f"Email: {ticket.camera_access_email}")
    if ticket.camera_access_details:
        lines.append(f"Камеры: {ticket.camera_access_details}")
    if ticket.key_count:
        lines.append(f"Кол-во ключей: {ticket.key_count}")
    if ticket.key_type:
        lines.append(f"Тип ключа: {ticket.key_type}")

    if ticket.assigned_master and hasattr(ticket.assigned_master, "full_name"):
        lines.append(f"\nМастер: {ticket.assigned_master.full_name}")

    if ticket.rating:
        lines.append(f"\nОценка: {ticket.rating}⭐")
        if ticket.rating_comment:
            lines.append(f"Комментарий: {ticket.rating_comment}")

    lines.append(f"\nСоздана: {ticket.created_at.strftime('%d.%m.%Y %H:%M')}")
    if ticket.completed_at:
        lines.append(f"Выполнена: {ticket.completed_at.strftime('%d.%m.%Y %H:%M')}")

    return "\n".join(lines)


def format_ticket_list_item(ticket: Ticket) -> str:
    status_name = STATUS_DISPLAY.get(ticket.status, ticket.status)
    category_name = CATEGORY_DISPLAY.get(ticket.category, ticket.category)
    return (
        f"<b>№{ticket.ticket_id}</b> — {status_name}\n"
        f"{category_name}\n"
        f"{ticket.created_at.strftime('%d.%m.%Y %H:%M')}"
    )


def format_history(entries: list[TicketHistory]) -> str:
    if not entries:
        return "История пуста."
    lines = ["<b>История заявки:</b>\n"]
    for entry in entries:
        status_name = STATUS_DISPLAY.get(entry.new_status, entry.new_status)
        ts = entry.changed_at.strftime("%d.%m.%Y %H:%M")
        role = entry.changed_by_role or ""
        line = f"• {ts} — <b>{status_name}</b>"
        if role:
            line += f" ({role})"
        if entry.comment:
            line += f"\n  {entry.comment}"
        lines.append(line)
    return "\n".join(lines)


def format_ticket_confirmation(data: dict) -> str:
    """Format ticket data collected from FSM for user confirmation."""
    complex_name = COMPLEX_DISPLAY.get(data.get("residential_complex", ""), data.get("residential_complex", ""))
    category_name = CATEGORY_DISPLAY.get(data.get("category", ""), data.get("category", ""))

    lines = [
        "<b>Проверьте заявку:</b>\n",
        f"ЖК: {complex_name}",
        f"Категория: {category_name}",
    ]

    if data.get("sub_category"):
        lines.append(f"Подкатегория: {data['sub_category']}")

    address_parts = []
    if data.get("block"):
        address_parts.append(f"блок {data['block']}")
    if data.get("entrance"):
        address_parts.append(f"подъезд {data['entrance']}")
    if data.get("apartment"):
        address_parts.append(f"кв. {data['apartment']}")
    if address_parts:
        lines.append(f"Адрес: {', '.join(address_parts)}")

    lines.append(f"Контакт: {data.get('client_full_name', '')}")
    lines.append(f"\nОписание: {data.get('description', '')}")

    if data.get("car_plate"):
        lines.append(f"Госномер: {data['car_plate']}")
    if data.get("car_gate"):
        lines.append(f"Заезд: {data['car_gate']}")
    if data.get("has_parking") is not None:
        lines.append(f"Есть паркинг: {'Да' if data['has_parking'] else 'Нет'}")
    if data.get("parking_reason"):
        lines.append(f"Причина: {data['parking_reason']}")
    if data.get("parking_contract_photo"):
        lines.append("📎 Договор паркинга: приложен")
    if data.get("parking_number"):
        lines.append(f"Номер паркинга: {data['parking_number']}")
    if data.get("camera_access_email"):
        lines.append(f"Email: {data['camera_access_email']}")
    if data.get("camera_access_details"):
        lines.append(f"Камеры: {data['camera_access_details']}")
    if data.get("key_count"):
        lines.append(f"Кол-во ключей: {data['key_count']}")
    if data.get("key_type"):
        lines.append(f"Тип ключа: {data['key_type']}")

    photo_count = len(data.get("attachments") or []) + len(data.get("face_id_photos") or [])
    if photo_count:
        lines.append(f"Фото: {photo_count} шт.")

    return "\n".join(lines)
