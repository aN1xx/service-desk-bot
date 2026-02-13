from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, String, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.db.base import Base, TimestampMixin


class Owner(Base, TimestampMixin):
    __tablename__ = "owners"

    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    residential_complex: Mapped[str] = mapped_column(String(50))
    block: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    entrance: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    apartment: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    telegram_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, unique=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    language: Mapped[str] = mapped_column(String(2), default="ru", server_default="ru")
