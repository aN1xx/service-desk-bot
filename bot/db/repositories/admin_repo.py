from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.admin import Admin


async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> Admin | None:
    result = await session.execute(
        select(Admin).where(Admin.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def get_all(session: AsyncSession) -> list[Admin]:
    result = await session.execute(select(Admin))
    return list(result.scalars().all())
