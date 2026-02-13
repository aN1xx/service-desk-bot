from typing import Optional

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from bot.db.base import Base, TimestampMixin


class BotText(Base, TimestampMixin):
    """Configurable bot text messages that can be edited via admin panel."""
    __tablename__ = "bot_texts"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), index=True)
    language: Mapped[str] = mapped_column(String(2), default="ru", server_default="ru")
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint("key", "language", name="uq_bot_texts_key_language"),
    )
