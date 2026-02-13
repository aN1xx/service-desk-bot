from aiogram import Router

from bot.filters.role import RoleFilter

admin_router = Router(name="admin")
admin_router.message.filter(RoleFilter(role="admin"))
admin_router.callback_query.filter(RoleFilter(role="admin"))

from bot.handlers.admin import menu, ticket_list, ticket_detail, reassign  # noqa: E402, F401
