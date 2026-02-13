from datetime import datetime, date

from sqlalchemy import select, update, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from bot.db.models.ticket import Ticket
from bot.db.models.ticket_history import TicketHistory


async def create(session: AsyncSession, **kwargs) -> Ticket:
    ticket = Ticket(**kwargs)
    session.add(ticket)
    await session.flush()
    return ticket


async def get_by_id(session: AsyncSession, ticket_pk: int) -> Ticket | None:
    result = await session.execute(
        select(Ticket).options(joinedload(Ticket.assigned_master)).where(Ticket.id == ticket_pk)
    )
    return result.scalar_one_or_none()


async def get_by_ticket_id(session: AsyncSession, ticket_id: str) -> Ticket | None:
    result = await session.execute(
        select(Ticket).options(joinedload(Ticket.assigned_master)).where(Ticket.ticket_id == ticket_id)
    )
    return result.scalar_one_or_none()


async def list_by_owner(
    session: AsyncSession, telegram_id: int, limit: int = 20, offset: int = 0
) -> list[Ticket]:
    result = await session.execute(
        select(Ticket)
        .where(Ticket.client_telegram_id == telegram_id)
        .order_by(desc(Ticket.created_at))
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def count_by_owner(session: AsyncSession, telegram_id: int) -> int:
    result = await session.execute(
        select(func.count(Ticket.id)).where(Ticket.client_telegram_id == telegram_id)
    )
    return result.scalar_one()


async def count_by_master(
    session: AsyncSession, master_id: int,
    status: str | None = None, statuses: list[str] | None = None
) -> int:
    q = select(func.count(Ticket.id)).where(Ticket.assigned_master_id == master_id)
    if statuses:
        q = q.where(Ticket.status.in_(statuses))
    elif status:
        q = q.where(Ticket.status == status)
    result = await session.execute(q)
    return result.scalar_one()


async def list_by_master(
    session: AsyncSession, master_id: int,
    status: str | None = None, statuses: list[str] | None = None,
    limit: int = 20, offset: int = 0
) -> list[Ticket]:
    q = select(Ticket).where(Ticket.assigned_master_id == master_id)
    if statuses:
        q = q.where(Ticket.status.in_(statuses))
    elif status:
        q = q.where(Ticket.status == status)
    q = q.order_by(desc(Ticket.created_at)).limit(limit).offset(offset)
    result = await session.execute(q)
    return list(result.scalars().all())


async def count_new_for_master(
    session: AsyncSession, residential_complexes: list[str]
) -> int:
    """Count NEW and PENDING_APPROVAL tickets (not assigned) for master's residential complexes."""
    q = select(func.count(Ticket.id)).where(
        Ticket.status.in_(["new", "pending_approval"]),
        Ticket.assigned_master_id.is_(None),
        Ticket.residential_complex.in_(residential_complexes),
    )
    result = await session.execute(q)
    return result.scalar_one()


async def list_new_for_master(
    session: AsyncSession, residential_complexes: list[str],
    limit: int = 20, offset: int = 0
) -> list[Ticket]:
    """List NEW and PENDING_APPROVAL tickets (not assigned) for master's residential complexes."""
    q = (
        select(Ticket)
        .where(
            Ticket.status.in_(["new", "pending_approval"]),
            Ticket.assigned_master_id.is_(None),
            Ticket.residential_complex.in_(residential_complexes),
        )
        .order_by(desc(Ticket.created_at))
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(q)
    return list(result.scalars().all())


async def list_filtered(
    session: AsyncSession,
    status: str | None = None,
    residential_complex: str | None = None,
    master_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Ticket]:
    q = select(Ticket)
    if status:
        q = q.where(Ticket.status == status)
    if residential_complex:
        q = q.where(Ticket.residential_complex == residential_complex)
    if master_id:
        q = q.where(Ticket.assigned_master_id == master_id)
    if date_from:
        q = q.where(func.date(Ticket.created_at) >= date_from)
    if date_to:
        q = q.where(func.date(Ticket.created_at) <= date_to)
    q = q.order_by(desc(Ticket.created_at)).limit(limit).offset(offset)
    result = await session.execute(q)
    return list(result.scalars().all())


async def count_filtered(
    session: AsyncSession,
    status: str | None = None,
    residential_complex: str | None = None,
    master_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> int:
    q = select(func.count(Ticket.id))
    if status:
        q = q.where(Ticket.status == status)
    if residential_complex:
        q = q.where(Ticket.residential_complex == residential_complex)
    if master_id:
        q = q.where(Ticket.assigned_master_id == master_id)
    if date_from:
        q = q.where(func.date(Ticket.created_at) >= date_from)
    if date_to:
        q = q.where(func.date(Ticket.created_at) <= date_to)
    result = await session.execute(q)
    return result.scalar_one()


async def update_status(session: AsyncSession, ticket_pk: int, new_status: str) -> None:
    values: dict = {"status": new_status, "updated_at": func.now()}
    if new_status == "completed":
        values["completed_at"] = func.now()
    await session.execute(update(Ticket).where(Ticket.id == ticket_pk).values(**values))


async def set_rating(
    session: AsyncSession, ticket_pk: int, rating: int, comment: str | None = None
) -> None:
    await session.execute(
        update(Ticket)
        .where(Ticket.id == ticket_pk)
        .values(rating=rating, rating_comment=comment, rated_at=func.now(), status="closed")
    )


async def reassign_master(session: AsyncSession, ticket_pk: int, master_id: int) -> None:
    await session.execute(
        update(Ticket).where(Ticket.id == ticket_pk).values(assigned_master_id=master_id)
    )


async def add_history(
    session: AsyncSession,
    ticket_pk: int,
    old_status: str | None,
    new_status: str,
    changed_by_id: int | None = None,
    changed_by_role: str | None = None,
    comment: str | None = None,
) -> None:
    entry = TicketHistory(
        ticket_id=ticket_pk,
        old_status=old_status,
        new_status=new_status,
        changed_by_id=changed_by_id,
        changed_by_role=changed_by_role,
        comment=comment,
    )
    session.add(entry)


async def get_history(session: AsyncSession, ticket_pk: int) -> list[TicketHistory]:
    result = await session.execute(
        select(TicketHistory)
        .where(TicketHistory.ticket_id == ticket_pk)
        .order_by(TicketHistory.changed_at)
    )
    return list(result.scalars().all())


async def get_approving_master_id(session: AsyncSession, ticket_pk: int) -> int | None:
    """Get the master telegram_id who approved a car plate ticket."""
    result = await session.execute(
        select(TicketHistory.changed_by_id)
        .where(
            TicketHistory.ticket_id == ticket_pk,
            TicketHistory.new_status == "master_approved",
            TicketHistory.changed_by_role == "master",
        )
        .order_by(TicketHistory.changed_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def count_today_by_owner(session: AsyncSession, telegram_id: int) -> int:
    today = date.today()
    result = await session.execute(
        select(func.count(Ticket.id)).where(
            Ticket.client_telegram_id == telegram_id,
            func.date(Ticket.created_at) == today,
        )
    )
    return result.scalar_one()


async def generate_ticket_id(session: AsyncSession) -> str:
    today = date.today()
    count = await session.execute(
        select(func.count(Ticket.id)).where(func.date(Ticket.created_at) == today)
    )
    num = count.scalar_one() + 1
    return f"QSS-{today.strftime('%Y%m%d')}-{num:04d}"
