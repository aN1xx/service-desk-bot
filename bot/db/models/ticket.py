from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, String, Text, Integer, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.db.base import Base, TimestampMixin


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    client_telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    client_phone: Mapped[str] = mapped_column(String(20))
    client_full_name: Mapped[str] = mapped_column(String(255))

    residential_complex: Mapped[str] = mapped_column(String(50), index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    sub_category: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    block: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    entrance: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    apartment: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    description: Mapped[str] = mapped_column(Text)
    attachments: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    face_id_photos: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    car_plate: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    car_gate: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    parking_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    has_parking: Mapped[Optional[bool]] = mapped_column(nullable=True)  # Does owner have parking?
    parking_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Reason if no parking
    parking_contract_photo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Contract file_id
    camera_access_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    camera_access_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    key_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    status: Mapped[str] = mapped_column(String(30), default="new", index=True)
    assigned_master_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("masters.id"), nullable=True
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rating_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rated_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    assigned_master = relationship("Master", foreign_keys=[assigned_master_id], lazy="joined")
