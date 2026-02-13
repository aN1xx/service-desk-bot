"""Language context for multi-language support."""

from contextvars import ContextVar

current_language: ContextVar[str] = ContextVar("current_language", default="ru")

SUPPORTED_LANGUAGES = ("ru", "kk")
DEFAULT_LANGUAGE = "ru"


def get_user_language(user_obj) -> str:
    """Extract language from user object with safe fallback."""
    if user_obj and hasattr(user_obj, "language"):
        return user_obj.language or DEFAULT_LANGUAGE
    return DEFAULT_LANGUAGE
