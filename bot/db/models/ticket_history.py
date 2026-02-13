from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, String, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.db.base import Base


class TicketHistory(Base):
    __tablename__ = "ticket_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), index=True)
    old_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30))
    changed_by_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    changed_by_role: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(server_default=func.now())
