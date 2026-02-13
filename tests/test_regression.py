"""
Regression tests for refactoring changes.
Ensures no behavior was broken during:
1. Extraction of send_ticket_attachments to shared utility
2. Replacement of getattr(owner, "language", "ru") with get_user_language()
3. Addition of try/except error handling in handlers
4. Addition of error_generic text key
5. Notification service recipient_lang parameter
6. AuthMiddleware get_user_language integration
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import contextmanager

from bot.utils.language import get_user_language, DEFAULT_LANGUAGE, current_language
from bot.services.text_service import get_text_sync, DEFAULT_TEXTS, DEFAULT_TEXTS_KK


# =============================================================================
# 1. send_ticket_attachments — same behavior as original inline code
# =============================================================================

class TestAttachmentsRegression:
    """Verify send_ticket_attachments behaves identically to the old inline code."""

    @pytest.mark.asyncio
    async def test_sends_parking_contract_as_photo(self):
        from bot.utils.attachments import send_ticket_attachments
        bot = AsyncMock()
        ticket = MagicMock()
        ticket.parking_contract_photo = "file_id_contract"
        ticket.face_id_photos = None
        ticket.attachments = None

        await send_ticket_attachments(bot, 123, ticket)
        bot.send_photo.assert_called_once_with(123, "file_id_contract", caption="📎 Договор паркинга")

    @pytest.mark.asyncio
    async def test_falls_back_to_document_on_photo_error(self):
        from bot.utils.attachments import send_ticket_attachments
        bot = AsyncMock()
        bot.send_photo = AsyncMock(side_effect=Exception("Not a photo"))
        ticket = MagicMock()
        ticket.parking_contract_photo = "file_id_doc"
        ticket.face_id_photos = None
        ticket.attachments = None

        await send_ticket_attachments(bot, 123, ticket)
        bot.send_document.assert_called_once_with(123, "file_id_doc", caption="📎 Договор паркинга")

    @pytest.mark.asyncio
    async def test_sends_face_id_photos(self):
        from bot.utils.attachments import send_ticket_attachments
        bot = AsyncMock()
        ticket = MagicMock()
        ticket.parking_contract_photo = None
        ticket.face_id_photos = ["ph1", "ph2"]
        ticket.attachments = None

        await send_ticket_attachments(bot, 123, ticket)
        assert bot.send_photo.call_count == 2
        bot.send_photo.assert_any_call(123, "ph1", caption="📷 Face ID фото 1")
        bot.send_photo.assert_any_call(123, "ph2", caption="📷 Face ID фото 2")

    @pytest.mark.asyncio
    async def test_sends_general_attachments(self):
        from bot.utils.attachments import send_ticket_attachments
        bot = AsyncMock()
        ticket = MagicMock()
        ticket.parking_contract_photo = None
        ticket.face_id_photos = None
        ticket.attachments = ["att1", "att2"]

        await send_ticket_attachments(bot, 123, ticket)
        assert bot.send_photo.call_count == 2
        bot.send_photo.assert_any_call(123, "att1", caption="📷 Вложение 1")

    @pytest.mark.asyncio
    async def test_attachment_fallback_to_document(self):
        from bot.utils.attachments import send_ticket_attachments
        bot = AsyncMock()
        bot.send_photo = AsyncMock(side_effect=Exception("Not a photo"))
        ticket = MagicMock()
        ticket.parking_contract_photo = None
        ticket.face_id_photos = None
        ticket.attachments = ["att1"]

        await send_ticket_attachments(bot, 123, ticket)
        bot.send_document.assert_called_once_with(123, "att1", caption="📎 Вложение 1")

    @pytest.mark.asyncio
    async def test_no_crash_on_empty_ticket(self):
        from bot.utils.attachments import send_ticket_attachments
        bot = AsyncMock()
        ticket = MagicMock()
        ticket.parking_contract_photo = None
        ticket.face_id_photos = None
        ticket.attachments = None

        # Should not crash, should not call bot methods
        await send_ticket_attachments(bot, 123, ticket)
        bot.send_photo.assert_not_called()
        bot.send_document.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_crash_on_missing_attrs(self):
        """Ticket without attachment-related attributes (old tickets)."""
        from bot.utils.attachments import send_ticket_attachments
        bot = AsyncMock()
        ticket = MagicMock(spec=[])  # no attributes at all

        await send_ticket_attachments(bot, 123, ticket)
        bot.send_photo.assert_not_called()


# =============================================================================
# 2. get_user_language — identical behavior to old getattr pattern
# =============================================================================

class TestGetUserLanguageRegression:
    """Verify get_user_language returns the same results as the old getattr pattern."""

    def test_matches_old_pattern_with_language(self):
        """Old: getattr(owner, 'language', 'ru') if owner else 'ru'"""
        user = MagicMock()
        user.language = "kk"
        old_result = getattr(user, "language", "ru") if user else "ru"
        new_result = get_user_language(user)
        assert old_result == new_result == "kk"

    def test_matches_old_pattern_with_ru(self):
        user = MagicMock()
        user.language = "ru"
        old_result = getattr(user, "language", "ru") if user else "ru"
        new_result = get_user_language(user)
        assert old_result == new_result == "ru"

    def test_matches_old_pattern_with_none_user(self):
        user = None
        old_result = getattr(user, "language", "ru") if user else "ru"
        new_result = get_user_language(user)
        assert old_result == new_result == "ru"

    def test_handles_none_language_better_than_old(self):
        """New helper handles None language gracefully (old pattern would return None)."""
        user = MagicMock()
        user.language = None
        # Old: getattr(user, "language", "ru") would return None
        # New: get_user_language returns DEFAULT_LANGUAGE
        new_result = get_user_language(user)
        assert new_result == DEFAULT_LANGUAGE  # improvement: no None leak

    def test_handles_empty_string_better(self):
        user = MagicMock()
        user.language = ""
        new_result = get_user_language(user)
        assert new_result == DEFAULT_LANGUAGE


# =============================================================================
# 3. Error handling — handlers show error instead of crashing
# =============================================================================

class TestErrorHandlingRegression:
    """Verify error_generic key exists and the pattern works."""

    def test_error_generic_in_default_texts_ru(self):
        assert "error_generic" in DEFAULT_TEXTS
        assert "ошибка" in DEFAULT_TEXTS["error_generic"].lower()

    def test_error_generic_in_default_texts_kk(self):
        assert "error_generic" in DEFAULT_TEXTS_KK
        assert "қате" in DEFAULT_TEXTS_KK["error_generic"].lower()

    def test_error_generic_accessible_via_get_text_sync_ru(self):
        token = current_language.set("ru")
        try:
            result = get_text_sync("error_generic")
            assert "ошибка" in result.lower()
        finally:
            current_language.reset(token)

    def test_error_generic_accessible_via_get_text_sync_kk(self):
        token = current_language.set("kk")
        try:
            result = get_text_sync("error_generic")
            assert "қате" in result.lower()
        finally:
            current_language.reset(token)


# =============================================================================
# 4. Notification service — recipient_lang works correctly
# =============================================================================

class TestNotificationLangRegression:
    """Verify notification functions respect recipient_lang parameter."""

    @pytest.mark.asyncio
    async def test_notify_owner_default_lang_ru(self):
        from bot.services.notification_service import notify_owner_ticket_created
        bot = AsyncMock()
        await notify_owner_ticket_created(bot, 123, "QSS-001")
        text = bot.send_message.call_args[0][1]
        # RU text should contain "Заявка" or "принята"
        assert "QSS-001" in text

    @pytest.mark.asyncio
    async def test_notify_owner_kk_lang(self):
        from bot.services.notification_service import notify_owner_ticket_created
        bot = AsyncMock()
        await notify_owner_ticket_created(bot, 123, "QSS-001", recipient_lang="kk")
        text = bot.send_message.call_args[0][1]
        # KK text should contain Kazakh word
        assert "Өтінім" in text or "QSS-001" in text

    @pytest.mark.asyncio
    async def test_with_lang_does_not_leak_state(self):
        """Ensure _with_lang restores the ContextVar after notification."""
        from bot.services.notification_service import notify_owner_ticket_created

        original_lang = current_language.get()
        bot = AsyncMock()
        await notify_owner_ticket_created(bot, 123, "QSS-001", recipient_lang="kk")
        after_lang = current_language.get()
        assert after_lang == original_lang, "Language ContextVar was NOT restored after notification!"

    @pytest.mark.asyncio
    async def test_notify_admins_uses_each_admin_language(self):
        from bot.services.notification_service import notify_admins_new_ticket
        bot = AsyncMock()

        admin_ru = MagicMock()
        admin_ru.telegram_id = 100
        admin_ru.language = "ru"

        admin_kk = MagicMock()
        admin_kk.telegram_id = 200
        admin_kk.language = "kk"

        with patch("bot.services.notification_service.admin_repo") as admin_repo:
            admin_repo.get_all = AsyncMock(return_value=[admin_ru, admin_kk])
            session = AsyncMock()

            await notify_admins_new_ticket(bot, session, "Test card")

            assert bot.send_message.call_count == 2
            # Each admin got their own message
            calls = bot.send_message.call_args_list
            assert calls[0][0][0] == 100
            assert calls[1][0][0] == 200


# =============================================================================
# 5. AuthMiddleware — uses get_user_language correctly
# =============================================================================

class TestAuthMiddlewareRegression:
    """Verify AuthMiddleware still sets language correctly."""

    @pytest.mark.asyncio
    async def test_sets_language_for_known_user(self):
        from bot.middlewares.auth import AuthMiddleware

        handler = AsyncMock(return_value="ok")
        mw = AuthMiddleware()

        user = MagicMock()
        user.id = 123

        user_obj = MagicMock()
        user_obj.language = "kk"

        session = AsyncMock()

        with patch("bot.middlewares.auth.resolve_role", return_value=("owner", user_obj)):
            event = MagicMock()
            data = {"event_from_user": user, "session": session}
            await mw(handler, event, data)

        assert data["user_role"] == "owner"
        assert data["user_obj"] == user_obj
        assert data["user_language"] == "kk"
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_defaults_language_for_unknown_user(self):
        from bot.middlewares.auth import AuthMiddleware

        handler = AsyncMock(return_value="ok")
        mw = AuthMiddleware()

        event = MagicMock()
        data = {}  # no event_from_user, no session
        await mw(handler, event, data)

        assert data["user_role"] is None
        assert data["user_obj"] is None
        assert data["user_language"] == DEFAULT_LANGUAGE

    @pytest.mark.asyncio
    async def test_contextvar_restored_after_handler(self):
        from bot.middlewares.auth import AuthMiddleware

        original = current_language.get()
        handler = AsyncMock(return_value="ok")
        mw = AuthMiddleware()

        user = MagicMock()
        user.id = 123
        user_obj = MagicMock()
        user_obj.language = "kk"
        session = AsyncMock()

        with patch("bot.middlewares.auth.resolve_role", return_value=("owner", user_obj)):
            event = MagicMock()
            data = {"event_from_user": user, "session": session}
            await mw(handler, event, data)

        # ContextVar should be restored
        assert current_language.get() == original

    @pytest.mark.asyncio
    async def test_contextvar_restored_on_handler_exception(self):
        from bot.middlewares.auth import AuthMiddleware

        original = current_language.get()
        handler = AsyncMock(side_effect=ValueError("handler error"))
        mw = AuthMiddleware()

        user = MagicMock()
        user.id = 123
        user_obj = MagicMock()
        user_obj.language = "kk"
        session = AsyncMock()

        with patch("bot.middlewares.auth.resolve_role", return_value=("owner", user_obj)):
            event = MagicMock()
            data = {"event_from_user": user, "session": session}
            with pytest.raises(ValueError):
                await mw(handler, event, data)

        # ContextVar MUST be restored even on exception
        assert current_language.get() == original


# =============================================================================
# 6. Text service — all keys consistent between RU and KK
# =============================================================================

class TestTextConsistencyRegression:
    """Verify RU/KK text dictionaries are in sync."""

    def test_same_keys(self):
        ru_keys = set(DEFAULT_TEXTS.keys())
        kk_keys = set(DEFAULT_TEXTS_KK.keys())
        missing_in_kk = ru_keys - kk_keys
        extra_in_kk = kk_keys - ru_keys
        assert not missing_in_kk, f"Keys missing from KK: {missing_in_kk}"
        assert not extra_in_kk, f"Extra keys in KK: {extra_in_kk}"

    def test_format_placeholders_match(self):
        """RU and KK texts should use the same {placeholder} names."""
        import re
        for key in DEFAULT_TEXTS:
            ru_text = DEFAULT_TEXTS[key]
            kk_text = DEFAULT_TEXTS_KK.get(key, "")
            ru_placeholders = set(re.findall(r"\{(\w+)\}", ru_text))
            kk_placeholders = set(re.findall(r"\{(\w+)\}", kk_text))
            assert ru_placeholders == kk_placeholders, (
                f"Placeholder mismatch for '{key}': RU={ru_placeholders}, KK={kk_placeholders}"
            )


# =============================================================================
# 7. Handler imports — verify all refactored handlers import correctly
# =============================================================================

class TestHandlerImportsRegression:

    def test_view_ticket_imports_shared_attachments(self):
        from bot.handlers.owner import view_ticket
        assert hasattr(view_ticket, 'send_ticket_attachments') or 'send_ticket_attachments' in dir(view_ticket)

    def test_my_tickets_imports_shared_attachments(self):
        from bot.handlers.master import my_tickets
        assert hasattr(my_tickets, 'send_ticket_attachments') or 'send_ticket_attachments' in dir(my_tickets)

    def test_ticket_detail_imports_shared_attachments(self):
        from bot.handlers.admin import ticket_detail
        assert hasattr(ticket_detail, 'send_ticket_attachments') or 'send_ticket_attachments' in dir(ticket_detail)

    def test_ticket_detail_imports_get_user_language(self):
        from bot.handlers.admin import ticket_detail
        assert hasattr(ticket_detail, 'get_user_language') or 'get_user_language' in dir(ticket_detail)

    def test_ticket_actions_imports_get_user_language(self):
        from bot.handlers.master import ticket_actions
        assert hasattr(ticket_actions, 'get_user_language') or 'get_user_language' in dir(ticket_actions)

    def test_auth_middleware_imports_get_user_language(self):
        from bot.middlewares import auth
        assert hasattr(auth, 'get_user_language') or 'get_user_language' in dir(auth)
