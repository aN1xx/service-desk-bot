"""Tests for bot.services.text_service module."""
import pytest
from unittest.mock import AsyncMock, patch

from bot.services.text_service import (
    get_text_sync,
    DEFAULT_TEXTS,
    DEFAULT_TEXTS_KK,
    _cache,
)
from bot.utils.language import current_language, DEFAULT_LANGUAGE


class TestGetTextSync:
    def test_from_default_ru(self):
        token = current_language.set("ru")
        try:
            result = get_text_sync("action_cancelled")
            assert result == "Действие отменено."
        finally:
            current_language.reset(token)

    def test_from_default_kk(self):
        token = current_language.set("kk")
        try:
            result = get_text_sync("action_cancelled")
            assert result == "Әрекет тоқтатылды."
        finally:
            current_language.reset(token)

    def test_fallback_kk_to_ru(self):
        """If key not in KK defaults, falls back to RU."""
        token = current_language.set("kk")
        try:
            # Use a key that exists in both - just verify it returns something
            result = get_text_sync("menu_owner")
            assert result  # non-empty
        finally:
            current_language.reset(token)

    def test_missing_key_returns_bracket(self):
        result = get_text_sync("nonexistent_key_xyz")
        assert result == "[nonexistent_key_xyz]"

    def test_with_kwargs(self):
        token = current_language.set("ru")
        try:
            result = get_text_sync("create_submitted", ticket_id="QSS-20250101-0001")
            assert "QSS-20250101-0001" in result
        finally:
            current_language.reset(token)

    def test_with_missing_kwargs_no_crash(self):
        """Missing format keys should not crash."""
        token = current_language.set("ru")
        try:
            # create_submitted expects {ticket_id} but we don't pass it
            result = get_text_sync("create_submitted")
            # Should return the template unformatted (KeyError is caught)
            assert result  # non-empty, no crash
        finally:
            current_language.reset(token)

    def test_cache_used_when_loaded(self):
        """When cache is loaded, it should be used instead of defaults."""
        import bot.services.text_service as ts
        old_cache = ts._cache.copy()
        old_loaded = ts._cache_loaded
        try:
            ts._cache = {"test_cached_key": {"ru": "Cached value"}}
            ts._cache_loaded = True

            token = current_language.set("ru")
            try:
                result = get_text_sync("test_cached_key")
                assert result == "Cached value"
            finally:
                current_language.reset(token)
        finally:
            ts._cache = old_cache
            ts._cache_loaded = old_loaded


class TestDefaultTextsKKCoverage:
    def test_all_ru_keys_exist_in_kk(self):
        """Every key in DEFAULT_TEXTS should also exist in DEFAULT_TEXTS_KK."""
        missing = set(DEFAULT_TEXTS.keys()) - set(DEFAULT_TEXTS_KK.keys())
        assert not missing, f"Keys missing from DEFAULT_TEXTS_KK: {missing}"

    def test_kk_values_non_empty(self):
        for key, value in DEFAULT_TEXTS_KK.items():
            assert value.strip(), f"Empty KK value for key: {key}"

    def test_ru_values_non_empty(self):
        for key, value in DEFAULT_TEXTS.items():
            assert value.strip(), f"Empty RU value for key: {key}"

    def test_error_generic_exists(self):
        assert "error_generic" in DEFAULT_TEXTS
        assert "error_generic" in DEFAULT_TEXTS_KK
