from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.master import Master


async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> Master | None:
    result = await session.execute(
        select(Master).where(Master.telegram_id == telegram_id, Master.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def get_by_id(session: AsyncSession, master_id: int) -> Master | None:
    result = await session.execute(select(Master).where(Master.id == master_id))
    return result.scalar_one_or_none()


async def get_by_complex(session: AsyncSession, residential_complex: str) -> list[Master]:
    result = await session.execute(
        select(Master).where(
            Master.residential_complex.contains(residential_complex),
            Master.is_active.is_(True),
        )
    )
    return list(result.scalars().all())


async def get_all_active(session: AsyncSession) -> list[Master]:
    result = await session.execute(select(Master).where(Master.is_active.is_(True)))
    return list(result.scalars().all())
