from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from bot.services.auth_service import resolve_role
from bot.utils.language import current_language, DEFAULT_LANGUAGE, get_user_language


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Extract user from the update
        user = data.get("event_from_user")
        session = data.get("session")

        if user and session:
            role, user_obj = await resolve_role(session, user.id)
            data["user_role"] = role
            data["user_obj"] = user_obj

            # Set language from user object
            lang = get_user_language(user_obj)
            data["user_language"] = lang
        else:
            data["user_role"] = None
            data["user_obj"] = None
            data["user_language"] = DEFAULT_LANGUAGE
            lang = DEFAULT_LANGUAGE

        token = current_language.set(lang)
        try:
            return await handler(event, data)
        finally:
            current_language.reset(token)
