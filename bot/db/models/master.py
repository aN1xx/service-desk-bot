from typing import Optional

from sqlalchemy import BigInteger, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from bot.db.base import Base, TimestampMixin


class Master(Base, TimestampMixin):
    __tablename__ = "masters"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    residential_complex: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    language: Mapped[str] = mapped_column(String(2), default="ru", server_default="ru")
