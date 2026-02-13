from aiogram import Router

from bot.filters.role import RoleFilter

master_router = Router(name="master")
master_router.message.filter(RoleFilter(role="master"))
master_router.callback_query.filter(RoleFilter(role="master"))

from bot.handlers.master import menu, ticket_actions, my_tickets  # noqa: E402, F401
