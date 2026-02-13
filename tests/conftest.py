"""Shared fixtures for all tests."""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def fake_owner():
    """Fake Owner object for unit tests."""
    owner = MagicMock()
    owner.id = 1
    owner.phone = "77001234567"
    owner.telegram_id = 123456
    owner.full_name = "Test Owner"
    owner.residential_complex = "alasha"
    owner.block = None
    owner.entrance = "3"
    owner.apartment = "42"
    owner.language = "ru"
    owner.is_active = True
    return owner


@pytest.fixture
def fake_master():
    """Fake Master object for unit tests."""
    master = MagicMock()
    master.id = 10
    master.telegram_id = 654321
    master.full_name = "Test Master"
    master.username = "testmaster"
    master.residential_complex = "alasha,terekti"
    master.is_active = True
    master.language = "ru"
    return master


@pytest.fixture
def fake_admin():
    """Fake Admin object for unit tests."""
    admin = MagicMock()
    admin.id = 100
    admin.telegram_id = 999999
    admin.full_name = "Test Admin"
    admin.language = "ru"
    return admin


@pytest.fixture
def fake_ticket():
    """Fake Ticket object for unit tests."""
    ticket = MagicMock()
    ticket.id = 1
    ticket.ticket_id = "QSS-20250101-0001"
    ticket.client_telegram_id = 123456
    ticket.client_phone = "77001234567"
    ticket.client_full_name = "Test Owner"
    ticket.residential_complex = "alasha"
    ticket.category = "cctv"
    ticket.sub_category = "Не работает камера / нет картинки"
    ticket.block = None
    ticket.entrance = "3"
    ticket.apartment = "42"
    ticket.description = "Камера не работает в подъезде"
    ticket.attachments = None
    ticket.face_id_photos = None
    ticket.car_plate = None
    ticket.car_gate = None
    ticket.has_parking = None
    ticket.parking_number = None
    ticket.parking_reason = None
    ticket.parking_contract_photo = None
    ticket.camera_access_email = None
    ticket.camera_access_details = None
    ticket.key_count = None
    ticket.key_type = None
    ticket.status = "new"
    ticket.assigned_master_id = None
    ticket.assigned_master = None
    ticket.completed_at = None
    ticket.rating = None
    ticket.rating_comment = None
    ticket.created_at = datetime(2025, 1, 1, 12, 0)
    return ticket


@pytest.fixture
def fake_ticket_car_plate(fake_ticket):
    """Fake Ticket with car plate data."""
    fake_ticket.category = "car_plate"
    fake_ticket.car_plate = "777ABC02"
    fake_ticket.car_gate = "2 заезд (центральный)"
    fake_ticket.has_parking = True
    fake_ticket.parking_number = "P-15"
    fake_ticket.parking_contract_photo = "file_id_contract"
    fake_ticket.description = "Договор паркинга приложен"
    fake_ticket.status = "pending_approval"
    return fake_ticket


@pytest.fixture
def fake_history_entry():
    """Fake TicketHistory entry."""
    entry = MagicMock()
    entry.id = 1
    entry.ticket_id = 1
    entry.old_status = None
    entry.new_status = "new"
    entry.changed_by_id = 123456
    entry.changed_by_role = "owner"
    entry.comment = "Заявка создана"
    entry.changed_at = datetime(2025, 1, 1, 12, 0)
    return entry


@pytest.fixture
def mock_session():
    """Mock AsyncSession for unit tests."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_bot():
    """Mock Bot for notification tests."""
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=MagicMock())
    bot.send_photo = AsyncMock(return_value=MagicMock())
    bot.send_document = AsyncMock(return_value=MagicMock())
    return bot
