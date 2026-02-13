"""Tests for bot.services.ticket_service module."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from bot.services.ticket_service import create_ticket, change_status, rate_ticket, find_master_for_ticket


class TestCreateTicket:
    @pytest.mark.asyncio
    async def test_create_ticket_basic(self, mock_session):
        fake_ticket = MagicMock()
        fake_ticket.id = 1
        fake_ticket.ticket_id = "QSS-20250101-0001"

        with patch("bot.services.ticket_service.ticket_repo") as ticket_repo:
            ticket_repo.generate_ticket_id = AsyncMock(return_value="QSS-20250101-0001")
            ticket_repo.create = AsyncMock(return_value=fake_ticket)
            ticket_repo.add_history = AsyncMock()

            data = {
                "client_telegram_id": 123456,
                "client_phone": "77001234567",
                "client_full_name": "Test Owner",
                "residential_complex": "alasha",
                "category": "cctv",
                "description": "Test description",
            }
            result = await create_ticket(mock_session, data)

            assert result.ticket_id == "QSS-20250101-0001"
            ticket_repo.create.assert_called_once()
            ticket_repo.add_history.assert_called_once()
            # Verify history has correct status
            call_kwargs = ticket_repo.add_history.call_args[1]
            assert call_kwargs["new_status"] == "new"
            assert call_kwargs["comment"] == "Заявка создана"

    @pytest.mark.asyncio
    async def test_create_ticket_car_plate_pending(self, mock_session):
        fake_ticket = MagicMock()
        fake_ticket.id = 2

        with patch("bot.services.ticket_service.ticket_repo") as ticket_repo:
            ticket_repo.generate_ticket_id = AsyncMock(return_value="QSS-20250101-0002")
            ticket_repo.create = AsyncMock(return_value=fake_ticket)
            ticket_repo.add_history = AsyncMock()

            data = {
                "client_telegram_id": 123456,
                "client_phone": "77001234567",
                "client_full_name": "Test Owner",
                "residential_complex": "alasha",
                "category": "car_plate",
                "description": "Договор приложен",
                "status": "pending_approval",
            }
            await create_ticket(mock_session, data)

            call_kwargs = ticket_repo.add_history.call_args[1]
            assert call_kwargs["new_status"] == "pending_approval"
            assert "госномер" in call_kwargs["comment"]

    @pytest.mark.asyncio
    async def test_create_ticket_enum_category(self, mock_session):
        """Enum category values should be converted to strings."""
        from bot.utils.constants import TicketCategory

        fake_ticket = MagicMock()
        fake_ticket.id = 1

        with patch("bot.services.ticket_service.ticket_repo") as ticket_repo:
            ticket_repo.generate_ticket_id = AsyncMock(return_value="QSS-20250101-0001")
            ticket_repo.create = AsyncMock(return_value=fake_ticket)
            ticket_repo.add_history = AsyncMock()

            data = {
                "client_telegram_id": 123456,
                "client_phone": "77001234567",
                "client_full_name": "Test",
                "residential_complex": "alasha",
                "category": TicketCategory.CCTV,
                "description": "Test",
            }
            await create_ticket(mock_session, data)

            create_kwargs = ticket_repo.create.call_args[1]
            assert create_kwargs["category"] == "cctv"


class TestChangeStatus:
    @pytest.mark.asyncio
    async def test_change_status(self, mock_session):
        with patch("bot.services.ticket_service.ticket_repo") as ticket_repo:
            ticket_repo.update_status = AsyncMock()
            ticket_repo.add_history = AsyncMock()

            await change_status(
                mock_session,
                ticket_pk=1,
                old_status="new",
                new_status="in_progress",
                changed_by_id=654321,
                changed_by_role="master",
                comment="Мастер принял заявку",
            )

            ticket_repo.update_status.assert_called_once_with(mock_session, 1, "in_progress")
            ticket_repo.add_history.assert_called_once()
            call_kwargs = ticket_repo.add_history.call_args[1]
            assert call_kwargs["old_status"] == "new"
            assert call_kwargs["new_status"] == "in_progress"


class TestRateTicket:
    @pytest.mark.asyncio
    async def test_rate_ticket(self, mock_session):
        with patch("bot.services.ticket_service.ticket_repo") as ticket_repo:
            ticket_repo.set_rating = AsyncMock()
            ticket_repo.add_history = AsyncMock()

            await rate_ticket(mock_session, ticket_pk=1, rating=5, comment="Great!")

            ticket_repo.set_rating.assert_called_once_with(mock_session, 1, 5, "Great!")
            call_kwargs = ticket_repo.add_history.call_args[1]
            assert "5/5" in call_kwargs["comment"]
            assert "Great!" in call_kwargs["comment"]

    @pytest.mark.asyncio
    async def test_rate_ticket_no_comment(self, mock_session):
        with patch("bot.services.ticket_service.ticket_repo") as ticket_repo:
            ticket_repo.set_rating = AsyncMock()
            ticket_repo.add_history = AsyncMock()

            await rate_ticket(mock_session, ticket_pk=1, rating=3)

            call_kwargs = ticket_repo.add_history.call_args[1]
            assert "3/5" in call_kwargs["comment"]


class TestFindMaster:
    @pytest.mark.asyncio
    async def test_find_master(self, mock_session, fake_master):
        with patch("bot.services.ticket_service.master_repo") as master_repo:
            master_repo.get_by_complex = AsyncMock(return_value=[fake_master])

            result = await find_master_for_ticket(mock_session, "alasha")
            assert result == fake_master.id

    @pytest.mark.asyncio
    async def test_find_master_no_match(self, mock_session):
        with patch("bot.services.ticket_service.master_repo") as master_repo:
            master_repo.get_by_complex = AsyncMock(return_value=[])

            result = await find_master_for_ticket(mock_session, "unknown_complex")
            assert result is None
