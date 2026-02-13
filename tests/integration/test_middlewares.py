"""Integration tests for middleware components."""
import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.middlewares.throttling import ThrottlingMiddleware


class TestThrottlingMiddleware:
    @pytest.mark.asyncio
    async def test_allows_first_message(self):
        mw = ThrottlingMiddleware(rate_limit=0.5)
        handler = AsyncMock(return_value="ok")

        event = MagicMock()
        event.__class__ = type("Message", (), {})  # isinstance check
        # Make it pass isinstance(event, Message) — we'll use a real-like mock
        from aiogram.types import Message
        event = MagicMock(spec=Message)
        event.from_user = MagicMock()
        event.from_user.id = 12345

        result = await mw(handler, event, {})
        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_blocks_fast_second_message(self):
        mw = ThrottlingMiddleware(rate_limit=0.5)
        handler = AsyncMock(return_value="ok")

        from aiogram.types import Message
        event = MagicMock(spec=Message)
        event.from_user = MagicMock()
        event.from_user.id = 12345

        await mw(handler, event, {})
        # Send immediately again
        result = await mw(handler, event, {})
        # Handler should only be called once (second blocked)
        assert handler.call_count == 1

    @pytest.mark.asyncio
    async def test_allows_after_delay(self):
        mw = ThrottlingMiddleware(rate_limit=0.1)
        handler = AsyncMock(return_value="ok")

        from aiogram.types import Message
        event = MagicMock(spec=Message)
        event.from_user = MagicMock()
        event.from_user.id = 12345

        await mw(handler, event, {})
        await asyncio.sleep(0.15)
        await mw(handler, event, {})
        assert handler.call_count == 2

    @pytest.mark.asyncio
    async def test_different_users_not_throttled(self):
        mw = ThrottlingMiddleware(rate_limit=0.5)
        handler = AsyncMock(return_value="ok")

        from aiogram.types import Message

        event1 = MagicMock(spec=Message)
        event1.from_user = MagicMock()
        event1.from_user.id = 111

        event2 = MagicMock(spec=Message)
        event2.from_user = MagicMock()
        event2.from_user.id = 222

        await mw(handler, event1, {})
        await mw(handler, event2, {})
        assert handler.call_count == 2

    @pytest.mark.asyncio
    async def test_non_message_events_pass_through(self):
        mw = ThrottlingMiddleware(rate_limit=0.5)
        handler = AsyncMock(return_value="ok")

        from aiogram.types import CallbackQuery
        event = MagicMock(spec=CallbackQuery)
        event.from_user = MagicMock()
        event.from_user.id = 12345

        await mw(handler, event, {})
        await mw(handler, event, {})
        # Both should pass (not throttled for non-Message)
        assert handler.call_count == 2
