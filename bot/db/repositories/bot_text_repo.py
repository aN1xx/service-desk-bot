from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models.bot_text import BotText


async def get_by_key(session: AsyncSession, key: str, language: str = "ru") -> str | None:
    """Get text value by key and language."""
    result = await session.execute(
        select(BotText.value).where(BotText.key == key, BotText.language == language)
    )
    return result.scalar_one_or_none()


async def get_all(session: AsyncSession) -> list[BotText]:
    """Get all bot texts."""
    result = await session.execute(
        select(BotText).order_by(BotText.key, BotText.language)
    )
    return list(result.scalars().all())


async def get_all_as_dict(session: AsyncSession) -> dict[str, dict[str, str]]:
    """Get all texts as {key: {lang: value}} nested dict."""
    result = await session.execute(select(BotText))
    d: dict[str, dict[str, str]] = {}
    for t in result.scalars().all():
        d.setdefault(t.key, {})[t.language] = t.value
    return d


async def upsert(
    session: AsyncSession,
    key: str,
    value: str,
    language: str = "ru",
    description: str | None = None,
) -> BotText:
    """Insert or update a text for a specific language."""
    result = await session.execute(
        select(BotText).where(BotText.key == key, BotText.language == language)
    )
    text = result.scalar_one_or_none()

    if text:
        text.value = value
        if description:
            text.description = description
    else:
        text = BotText(key=key, language=language, value=value, description=description)
        session.add(text)

    return text


async def update_value(session: AsyncSession, text_id: int, value: str) -> bool:
    """Update text value by ID."""
    result = await session.execute(
        select(BotText).where(BotText.id == text_id)
    )
    text = result.scalar_one_or_none()
    if text:
        text.value = value
        return True
    return False
