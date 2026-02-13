"""Tests for bot.utils.formatting module."""
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from bot.utils.formatting import format_ticket_card, format_history, format_ticket_confirmation


class TestFormatTicketCard:
    def test_basic_ticket_card(self, fake_ticket):
        result = format_ticket_card(fake_ticket)
        assert "QSS-20250101-0001" in result
        assert "Новая" in result  # STATUS_DISPLAY for "new"
        assert "ЖК Alasha Residence" in result
        assert "Системы видеонаблюдения" in result
        assert "подъезд 3" in result
        assert "кв. 42" in result
        assert "Камера не работает" in result
        assert "01.01.2025 12:00" in result

    def test_card_with_client(self, fake_ticket):
        result = format_ticket_card(fake_ticket, include_client=True)
        assert "Test Owner" in result
        assert "77001234567" in result

    def test_card_without_client(self, fake_ticket):
        result = format_ticket_card(fake_ticket, include_client=False)
        assert "Клиент:" not in result
        assert "Телефон:" not in result

    def test_card_with_master(self, fake_ticket):
        master = MagicMock()
        master.full_name = "Master Name"
        fake_ticket.assigned_master = master
        result = format_ticket_card(fake_ticket)
        assert "Мастер: Master Name" in result

    def test_card_with_rating(self, fake_ticket):
        fake_ticket.rating = 5
        fake_ticket.rating_comment = "Отличная работа!"
        result = format_ticket_card(fake_ticket)
        assert "5⭐" in result
        assert "Отличная работа!" in result

    def test_card_car_plate(self, fake_ticket_car_plate):
        result = format_ticket_card(fake_ticket_car_plate)
        assert "777ABC02" in result
        assert "2 заезд (центральный)" in result
        assert "Да" in result  # has_parking=True
        assert "P-15" in result

    def test_card_with_sub_category(self, fake_ticket):
        result = format_ticket_card(fake_ticket)
        assert "Подкатегория:" in result

    def test_card_with_block(self, fake_ticket):
        fake_ticket.block = "15"
        result = format_ticket_card(fake_ticket)
        assert "блок 15" in result

    def test_card_completed_at(self, fake_ticket):
        fake_ticket.completed_at = datetime(2025, 1, 2, 14, 30)
        result = format_ticket_card(fake_ticket)
        assert "Выполнена: 02.01.2025 14:30" in result

    def test_card_camera_access(self, fake_ticket):
        fake_ticket.camera_access_email = "test@mail.kz"
        fake_ticket.camera_access_details = "Блок 5, подъезд 2"
        result = format_ticket_card(fake_ticket)
        assert "test@mail.kz" in result
        assert "Блок 5, подъезд 2" in result

    def test_card_key_magnet(self, fake_ticket):
        fake_ticket.key_count = 3
        fake_ticket.key_type = "Новый (800 тг/шт)"
        result = format_ticket_card(fake_ticket)
        assert "Кол-во ключей: 3" in result
        assert "Новый (800 тг/шт)" in result


class TestFormatHistory:
    def test_empty_history(self):
        result = format_history([])
        assert result == "История пуста."

    def test_single_entry(self, fake_history_entry):
        result = format_history([fake_history_entry])
        assert "История заявки" in result
        assert "Новая" in result
        assert "owner" in result
        assert "Заявка создана" in result
        assert "01.01.2025 12:00" in result

    def test_multiple_entries(self, fake_history_entry):
        entry2 = MagicMock()
        entry2.new_status = "in_progress"
        entry2.changed_at = datetime(2025, 1, 1, 13, 0)
        entry2.changed_by_role = "master"
        entry2.comment = "Мастер принял заявку"

        result = format_history([fake_history_entry, entry2])
        assert "Новая" in result
        assert "В работе" in result
        assert "Мастер принял заявку" in result

    def test_entry_without_role(self, fake_history_entry):
        fake_history_entry.changed_by_role = None
        result = format_history([fake_history_entry])
        assert "()" not in result  # no empty parens

    def test_entry_without_comment(self, fake_history_entry):
        fake_history_entry.comment = None
        result = format_history([fake_history_entry])
        assert "Новая" in result


class TestFormatTicketConfirmation:
    def test_confirmation_basic(self):
        data = {
            "residential_complex": "alasha",
            "category": "cctv",
            "entrance": "3",
            "apartment": "42",
            "client_full_name": "Test Owner",
            "description": "Камера не работает",
        }
        result = format_ticket_confirmation(data)
        assert "Проверьте заявку" in result
        assert "ЖК Alasha Residence" in result
        assert "Системы видеонаблюдения" in result
        assert "подъезд 3" in result
        assert "кв. 42" in result
        assert "Камера не работает" in result

    def test_confirmation_with_block(self):
        data = {
            "residential_complex": "terekti",
            "category": "key_magnet",
            "block": "15",
            "entrance": "2",
            "apartment": "10",
            "client_full_name": "Owner",
            "description": "Нужен ключ",
        }
        result = format_ticket_confirmation(data)
        assert "блок 15" in result

    def test_confirmation_car_plate(self):
        data = {
            "residential_complex": "alasha",
            "category": "car_plate",
            "entrance": "3",
            "apartment": "42",
            "client_full_name": "Owner",
            "description": "Договор приложен",
            "car_plate": "777ABC02",
            "car_gate": "2 заезд",
            "has_parking": True,
            "parking_contract_photo": "file_id_123",
            "parking_number": "P-15",
        }
        result = format_ticket_confirmation(data)
        assert "777ABC02" in result
        assert "2 заезд" in result
        assert "Да" in result
        assert "Договор паркинга: приложен" in result
        assert "P-15" in result

    def test_confirmation_with_photos(self):
        data = {
            "residential_complex": "alasha",
            "category": "face_id",
            "entrance": "1",
            "apartment": "1",
            "client_full_name": "Owner",
            "description": "Добавить в базу",
            "face_id_photos": ["photo1", "photo2", "photo3"],
        }
        result = format_ticket_confirmation(data)
        assert "Фото: 3 шт." in result

    def test_confirmation_with_attachments_and_face_photos(self):
        data = {
            "residential_complex": "alasha",
            "category": "other",
            "entrance": "1",
            "apartment": "1",
            "client_full_name": "Owner",
            "description": "Something",
            "attachments": ["a1", "a2"],
            "face_id_photos": ["f1"],
        }
        result = format_ticket_confirmation(data)
        assert "Фото: 3 шт." in result

    def test_confirmation_camera_access(self):
        data = {
            "residential_complex": "alasha",
            "category": "camera_access",
            "entrance": "1",
            "apartment": "1",
            "client_full_name": "Owner",
            "description": "Доступ к камерам",
            "camera_access_email": "test@mail.kz",
            "camera_access_details": "Блок 5",
        }
        result = format_ticket_confirmation(data)
        assert "test@mail.kz" in result
        assert "Блок 5" in result
