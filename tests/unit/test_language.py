"""Tests for bot.utils.language module."""
import pytest
from unittest.mock import MagicMock

from bot.utils.language import get_user_language, DEFAULT_LANGUAGE, current_language


class TestGetUserLanguage:
    def test_returns_user_language(self):
        user = MagicMock()
        user.language = "kk"
        assert get_user_language(user) == "kk"

    def test_returns_default_for_none_user(self):
        assert get_user_language(None) == DEFAULT_LANGUAGE

    def test_returns_default_for_no_language_attr(self):
        user = MagicMock(spec=[])  # no attributes
        assert get_user_language(user) == DEFAULT_LANGUAGE

    def test_returns_default_for_empty_language(self):
        user = MagicMock()
        user.language = ""
        assert get_user_language(user) == DEFAULT_LANGUAGE

    def test_returns_default_for_none_language(self):
        user = MagicMock()
        user.language = None
        assert get_user_language(user) == DEFAULT_LANGUAGE

    def test_returns_ru(self):
        user = MagicMock()
        user.language = "ru"
        assert get_user_language(user) == "ru"
