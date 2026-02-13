import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from bot.config import settings
from bot.db.engine import session_pool
from bot.middlewares.db_session import DbSessionMiddleware
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.handlers import get_all_routers

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_migrations() -> None:
    import signal

    def _timeout_handler(signum, frame):
        raise TimeoutError("Migration timed out")

    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.db_url)

    try:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(15)  # 15 second timeout
        command.upgrade(alembic_cfg, "head")
        signal.alarm(0)
    except TimeoutError:
        logger.warning("Migration timed out — assuming DB is already up to date")
    except Exception as e:
        logger.warning("Migration failed: %s — continuing", e)


async def seed_and_load_texts() -> None:
    """Seed default texts and load cache."""
    from bot.services import text_service

    async with session_pool() as session:
        count = await text_service.seed_default_texts(session)
        await session.commit()
        if count:
            logger.info("Seeded %d default bot texts", count)
        await text_service.load_cache(session)


async def main() -> None:
    # Seed texts and load cache
    await seed_and_load_texts()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.outer_middleware(DbSessionMiddleware(session_pool))
    dp.update.outer_middleware(AuthMiddleware())
    dp.message.middleware(ThrottlingMiddleware())

    for router in get_all_routers():
        dp.include_router(router)

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Главное меню"),
            BotCommand(command="help", description="Помощь"),
            BotCommand(command="cancel", description="Отменить действие"),
        ],
        scope=BotCommandScopeDefault(),
    )

    logger.info("Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Migrations are run separately via: make migrate
    # run_migrations() is disabled to avoid asyncpg hanging issue
    asyncio.run(main())
