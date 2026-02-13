from aiogram.filters.callback_data import CallbackData


class PageCB(CallbackData, prefix="page"):
    scope: str   # owner_tickets, master_tickets, admin_tickets
    page: int


class BackCB(CallbackData, prefix="back"):
    target: str  # main_menu, owner_menu, master_menu, admin_menu


# --- Menu navigation callbacks ---

class MenuCB(CallbackData, prefix="menu"):
    """Main menu navigation for all roles."""
    action: str  # owner, master, admin


class OwnerMenuCB(CallbackData, prefix="om"):
    """Owner menu actions."""
    action: str  # create, tickets, instructions


class MasterMenuCB(CallbackData, prefix="mm"):
    """Master menu actions."""
    action: str  # new, active, completed


class AdminMenuCB(CallbackData, prefix="am"):
    """Admin menu actions."""
    action: str  # all, new, progress, completed, closed, filter_complex, filter_master, filter_date


class CancelCB(CallbackData, prefix="x"):
    """Cancel action."""
    pass


class LanguageCB(CallbackData, prefix="lang"):
    """Language selection."""
    lang: str  # "ru" or "kk"
