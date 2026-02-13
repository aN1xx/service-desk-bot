"""Seed test data for development.

Run: docker compose exec bot python -m scripts.seed_data
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.engine import engine, session_pool
from bot.db.models import Owner, Master, Admin


OWNERS = [
    {
        "phone": "77001234567",
        "full_name": "Иванов Иван Иванович",
        "residential_complex": "alasha",
        "entrance": "1",
        "apartment": "10",
    },
    {
        "phone": "77001234568",
        "full_name": "Петрова Мария Сергеевна",
        "residential_complex": "terekti",
        "block": "3",
        "entrance": "1",
        "apartment": "25",
    },
    {
        "phone": "77001234569",
        "full_name": "Сидоров Алексей Петрович",
        "residential_complex": "kemel",
        "block": "7",
        "entrance": "2",
        "apartment": "44",
    },
    {
        "phone": "77001234570",
        "full_name": "Касымова Айгуль Нурлановна",
        "residential_complex": "jana_omir",
        "block": "2",
        "entrance": "1",
        "apartment": "15",
    },
]

# Replace telegram_id with real IDs for testing
MASTERS = [
    {
        "telegram_id": 100000001,
        "full_name": "Мастер Алаша",
        "username": "master_alasha",
        "residential_complex": "alasha",
    },
    {
        "telegram_id": 100000002,
        "full_name": "Мастер Теректи",
        "username": "master_terekti",
        "residential_complex": "terekti,kemel,jana_omir",
    },
]

ADMINS = [
    {
        "telegram_id": 100000003,
        "full_name": "Руководитель Сервисной Службы",
    },
]


async def seed() -> None:
    async with session_pool() as session:
        # Owners
        for data in OWNERS:
            exists = await session.execute(
                select(Owner).where(Owner.phone == data["phone"])
            )
            if not exists.scalar_one_or_none():
                session.add(Owner(**data))

        # Masters
        for data in MASTERS:
            exists = await session.execute(
                select(Master).where(Master.telegram_id == data["telegram_id"])
            )
            if not exists.scalar_one_or_none():
                session.add(Master(**data))

        # Admins
        for data in ADMINS:
            exists = await session.execute(
                select(Admin).where(Admin.telegram_id == data["telegram_id"])
            )
            if not exists.scalar_one_or_none():
                session.add(Admin(**data))

        await session.commit()
        print("Seed data inserted successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
