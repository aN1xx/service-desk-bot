from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.repositories import ticket_repo


async def generate(session: AsyncSession) -> str:
    return await ticket_repo.generate_ticket_id(session)
