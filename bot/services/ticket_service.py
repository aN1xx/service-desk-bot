import logging

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.repositories import ticket_repo, master_repo

logger = logging.getLogger(__name__)

MAX_TICKETS_PER_DAY = 10


async def check_daily_limit(session: AsyncSession, telegram_id: int) -> tuple[bool, int]:
    """Check if owner exceeded daily ticket limit.

    Returns (allowed, current_count).
    """
    count = await ticket_repo.count_today_by_owner(session, telegram_id)
    return count < MAX_TICKETS_PER_DAY, count


async def reassign_ticket(
    session: AsyncSession,
    ticket_pk: int,
    master_id: int,
    current_status: str,
    changed_by_id: int,
    master_name: str,
) -> None:
    """Reassign a ticket to a different master and record the change in history."""
    await ticket_repo.reassign_master(session, ticket_pk, master_id)
    await ticket_repo.add_history(
        session,
        ticket_pk=ticket_pk,
        old_status=current_status,
        new_status=current_status,
        changed_by_id=changed_by_id,
        changed_by_role="admin",
        comment=f"Мастер изменен на: {master_name}",
    )
    logger.info("Ticket #%d reassigned to master %d by %d", ticket_pk, master_id, changed_by_id)


async def create_ticket(session: AsyncSession, data: dict) -> "Ticket":
    """Create a new ticket from collected FSM data."""
    from bot.db.models.ticket import Ticket

    ticket_id = await ticket_repo.generate_ticket_id(session)

    # Convert enums to strings if needed
    status = data.get("status", "new")
    if hasattr(status, "value"):
        status = status.value

    category = data["category"]
    if hasattr(category, "value"):
        category = category.value

    ticket = await ticket_repo.create(
        session,
        ticket_id=ticket_id,
        client_telegram_id=data["client_telegram_id"],
        client_phone=data["client_phone"],
        client_full_name=data["client_full_name"],
        residential_complex=data["residential_complex"],
        category=category,
        sub_category=data.get("sub_category"),
        block=data.get("block"),
        entrance=data.get("entrance"),
        apartment=data.get("apartment"),
        description=data["description"],
        attachments=data.get("attachments"),
        face_id_photos=data.get("face_id_photos"),
        car_plate=data.get("car_plate"),
        car_gate=data.get("car_gate"),
        has_parking=data.get("has_parking"),
        parking_number=data.get("parking_number"),
        parking_reason=data.get("parking_reason"),
        parking_contract_photo=data.get("parking_contract_photo"),
        camera_access_email=data.get("camera_access_email"),
        camera_access_details=data.get("camera_access_details"),
        key_count=data.get("key_count"),
        key_type=data.get("key_type"),
        status=status,
        assigned_master_id=data.get("assigned_master_id"),
    )

    # Use correct status for history
    history_comment = "Заявка создана"
    if status == "pending_approval":
        history_comment = "Заявка на госномер создана, ожидает одобрения"

    await ticket_repo.add_history(
        session,
        ticket_pk=ticket.id,
        old_status=None,
        new_status=status,
        changed_by_id=data["client_telegram_id"],
        changed_by_role="owner",
        comment=history_comment,
    )

    logger.info("Ticket %s created by %s", ticket_id, data["client_telegram_id"])
    return ticket


async def find_master_for_ticket(session: AsyncSession, residential_complex: str) -> int | None:
    """Find an active master assigned to the given residential complex."""
    masters = await master_repo.get_by_complex(session, residential_complex)
    if masters:
        return masters[0].id
    return None


async def change_status(
    session: AsyncSession,
    ticket_pk: int,
    old_status: str,
    new_status: str,
    changed_by_id: int,
    changed_by_role: str,
    comment: str | None = None,
) -> None:
    await ticket_repo.update_status(session, ticket_pk, new_status)
    await ticket_repo.add_history(
        session,
        ticket_pk=ticket_pk,
        old_status=old_status,
        new_status=new_status,
        changed_by_id=changed_by_id,
        changed_by_role=changed_by_role,
        comment=comment,
    )
    logger.info("Ticket #%d status: %s -> %s by %s", ticket_pk, old_status, new_status, changed_by_id)


async def rate_ticket(
    session: AsyncSession, ticket_pk: int, rating: int, comment: str | None = None
) -> None:
    await ticket_repo.set_rating(session, ticket_pk, rating, comment)
    await ticket_repo.add_history(
        session,
        ticket_pk=ticket_pk,
        old_status="completed",
        new_status="closed",
        comment=f"Оценка: {rating}/5" + (f" — {comment}" if comment else ""),
    )
    logger.info("Ticket #%d rated %d/5", ticket_pk, rating)
