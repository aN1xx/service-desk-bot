from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from bot.config import settings

engine = create_async_engine(settings.db_url, echo=False)
session_pool = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
