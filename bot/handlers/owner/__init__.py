from aiogram import Router

from bot.filters.role import RoleFilter

owner_router = Router(name="owner")
owner_router.message.filter(RoleFilter(role="owner"))
owner_router.callback_query.filter(RoleFilter(role="owner"))

from bot.handlers.owner import menu, create_ticket, view_ticket, rate_ticket  # noqa: E402, F401
