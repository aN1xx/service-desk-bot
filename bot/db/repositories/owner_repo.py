from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.owner import Owner


async def get_by_phone(session: AsyncSession, phone: str) -> Owner | None:
    result = await session.execute(select(Owner).where(Owner.phone == phone, Owner.is_active.is_(True)))
    return result.scalar_one_or_none()


async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> Owner | None:
    result = await session.execute(
        select(Owner).where(Owner.telegram_id == telegram_id, Owner.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def link_telegram_id(session: AsyncSession, owner_id: int, telegram_id: int) -> None:
    await session.execute(
        update(Owner).where(Owner.id == owner_id).values(telegram_id=telegram_id)
    )
