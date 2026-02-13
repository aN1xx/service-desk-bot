from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from bot.db.base import Base, TimestampMixin


class Admin(Base, TimestampMixin):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(2), default="ru", server_default="ru")
