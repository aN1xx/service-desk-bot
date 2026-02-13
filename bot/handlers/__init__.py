from aiogram import Router


def get_all_routers() -> list[Router]:
    from bot.handlers.common import router as common_router
    from bot.handlers.owner import owner_router
    from bot.handlers.master import master_router
    from bot.handlers.admin import admin_router

    return [common_router, owner_router, master_router, admin_router]
