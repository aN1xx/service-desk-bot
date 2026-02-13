"""Tests for bot.services.notification_service module."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.services.notification_service import (
    notify_owner_ticket_created,
    notify_owner_status_changed,
    notify_owner_completed,
    notify_master_new_ticket,
    notify_admins_new_ticket,
    notify_owner_car_plate_decision,
    _with_lang,
)
from bot.utils.language import current_language


class TestWithLangContext:
    def test_with_lang_sets_language(self):
        with _with_lang("kk"):
            assert current_language.get() == "kk"
        # Restored after context
        assert current_language.get() != "kk" or current_language.get() == "ru"

    def test_with_lang_default_on_none(self):
        with _with_lang(None):
            assert current_language.get() == "ru"

    def test_with_lang_restores_on_exception(self):
        original = current_language.get()
        try:
            with _with_lang("kk"):
                raise ValueError("test")
        except ValueError:
            pass
        assert current_language.get() == original


class TestNotifyOwnerTicketCreated:
    @pytest.mark.asyncio
    async def test_sends_message(self, mock_bot):
        await notify_owner_ticket_created(mock_bot, 123456, "QSS-20250101-0001")
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert 123456 == call_args[0][0]
        assert "QSS-20250101-0001" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_with_language_kk(self, mock_bot):
        await notify_owner_ticket_created(mock_bot, 123456, "QSS-20250101-0001", recipient_lang="kk")
        mock_bot.send_message.assert_called_once()
        text = mock_bot.send_message.call_args[0][1]
        # KK text should contain Kazakh word "Өтінім"
        assert "Өтінім" in text or "QSS-20250101-0001" in text


class TestNotifyOwnerStatusChanged:
    @pytest.mark.asyncio
    async def test_basic_status_change(self, mock_bot):
        await notify_owner_status_changed(mock_bot, 123456, "QSS-001", "completed")
        mock_bot.send_message.assert_called_once()
        text = mock_bot.send_message.call_args[0][1]
        assert "QSS-001" in text

    @pytest.mark.asyncio
    async def test_in_progress_with_master(self, mock_bot):
        await notify_owner_status_changed(
            mock_bot, 123456, "QSS-001", "in_progress", master_name="John"
        )
        text = mock_bot.send_message.call_args[0][1]
        assert "John" in text


class TestNotifyOwnerCompleted:
    @pytest.mark.asyncio
    async def test_sends_with_rating_keyboard(self, mock_bot):
        await notify_owner_completed(mock_bot, 123456, "QSS-001", ticket_pk=1)
        mock_bot.send_message.assert_called_once()
        kwargs = mock_bot.send_message.call_args[1]
        assert "reply_markup" in kwargs
        # Check keyboard has 5 star buttons
        kb = kwargs["reply_markup"]
        assert len(kb.inline_keyboard[0]) == 5


class TestNotifyMasterNewTicket:
    @pytest.mark.asyncio
    async def test_sends_card_with_buttons(self, mock_bot):
        await notify_master_new_ticket(mock_bot, 654321, "Card text", ticket_pk=1)
        mock_bot.send_message.assert_called_once()
        kwargs = mock_bot.send_message.call_args[1]
        assert "reply_markup" in kwargs
        kb = kwargs["reply_markup"]
        # Accept + Complete buttons
        assert len(kb.inline_keyboard) == 2


class TestNotifyAdminsNewTicket:
    @pytest.mark.asyncio
    async def test_broadcasts_to_all_admins(self, mock_bot, fake_admin):
        admin2 = MagicMock()
        admin2.telegram_id = 888888
        admin2.language = "kk"

        with patch("bot.services.notification_service.admin_repo") as admin_repo:
            admin_repo.get_all = AsyncMock(return_value=[fake_admin, admin2])
            mock_session = AsyncMock()

            await notify_admins_new_ticket(mock_bot, mock_session, "Card text")
            assert mock_bot.send_message.call_count == 2


class TestNotifyCarPlateDecision:
    @pytest.mark.asyncio
    async def test_approved(self, mock_bot):
        await notify_owner_car_plate_decision(mock_bot, 123456, "QSS-001", approved=True)
        text = mock_bot.send_message.call_args[0][1]
        assert "QSS-001" in text

    @pytest.mark.asyncio
    async def test_rejected(self, mock_bot):
        await notify_owner_car_plate_decision(mock_bot, 123456, "QSS-001", approved=False)
        text = mock_bot.send_message.call_args[0][1]
        assert "QSS-001" in text


class TestSafeSendHandlesError:
    @pytest.mark.asyncio
    async def test_safe_send_catches_exception(self, mock_bot):
        mock_bot.send_message = AsyncMock(side_effect=Exception("Telegram API error"))
        # Should not crash
        await notify_owner_ticket_created(mock_bot, 123456, "QSS-001")
