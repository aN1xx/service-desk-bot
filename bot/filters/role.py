from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject


class RoleFilter(BaseFilter):
    def __init__(self, role: str) -> None:
        self.role = role

    async def __call__(self, event: TelegramObject, user_role: str | None = None, **kwargs) -> bool:
        return user_role == self.role
