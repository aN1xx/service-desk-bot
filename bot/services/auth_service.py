from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.repositories import owner_repo, master_repo, admin_repo
from bot.utils.constants import UserRole


async def resolve_role(session: AsyncSession, telegram_id: int) -> tuple[str | None, object | None]:
    """Return (role, user_object) for the given Telegram ID.

    Priority: admin > master > owner.
    """
    admin = await admin_repo.get_by_telegram_id(session, telegram_id)
    if admin:
        return UserRole.ADMIN, admin

    master = await master_repo.get_by_telegram_id(session, telegram_id)
    if master:
        return UserRole.MASTER, master

    owner = await owner_repo.get_by_telegram_id(session, telegram_id)
    if owner:
        return UserRole.OWNER, owner

    return None, None


async def authenticate_by_phone(
    session: AsyncSession, phone: str, telegram_id: int
) -> tuple[str | None, object | None]:
    """Look up phone in owners table, link telegram_id if found."""
    owner = await owner_repo.get_by_phone(session, phone)
    if owner:
        await owner_repo.link_telegram_id(session, owner.id, telegram_id)
        # Check if also admin or master
        admin = await admin_repo.get_by_telegram_id(session, telegram_id)
        if admin:
            return UserRole.ADMIN, admin
        master = await master_repo.get_by_telegram_id(session, telegram_id)
        if master:
            return UserRole.MASTER, master
        return UserRole.OWNER, owner
    return None, None
