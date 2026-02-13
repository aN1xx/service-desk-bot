"""Tests for bot.services.auth_service module."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from bot.services.auth_service import resolve_role, authenticate_by_phone
from bot.utils.constants import UserRole


class TestResolveRole:
    @pytest.mark.asyncio
    async def test_resolve_role_admin(self, mock_session, fake_admin):
        with patch("bot.services.auth_service.admin_repo") as admin_repo, \
             patch("bot.services.auth_service.master_repo"), \
             patch("bot.services.auth_service.owner_repo"):
            admin_repo.get_by_telegram_id = AsyncMock(return_value=fake_admin)

            role, user_obj = await resolve_role(mock_session, 999999)
            assert role == UserRole.ADMIN
            assert user_obj == fake_admin

    @pytest.mark.asyncio
    async def test_resolve_role_master(self, mock_session, fake_master):
        with patch("bot.services.auth_service.admin_repo") as admin_repo, \
             patch("bot.services.auth_service.master_repo") as master_repo, \
             patch("bot.services.auth_service.owner_repo"):
            admin_repo.get_by_telegram_id = AsyncMock(return_value=None)
            master_repo.get_by_telegram_id = AsyncMock(return_value=fake_master)

            role, user_obj = await resolve_role(mock_session, 654321)
            assert role == UserRole.MASTER
            assert user_obj == fake_master

    @pytest.mark.asyncio
    async def test_resolve_role_owner(self, mock_session, fake_owner):
        with patch("bot.services.auth_service.admin_repo") as admin_repo, \
             patch("bot.services.auth_service.master_repo") as master_repo, \
             patch("bot.services.auth_service.owner_repo") as owner_repo:
            admin_repo.get_by_telegram_id = AsyncMock(return_value=None)
            master_repo.get_by_telegram_id = AsyncMock(return_value=None)
            owner_repo.get_by_telegram_id = AsyncMock(return_value=fake_owner)

            role, user_obj = await resolve_role(mock_session, 123456)
            assert role == UserRole.OWNER
            assert user_obj == fake_owner

    @pytest.mark.asyncio
    async def test_resolve_role_none(self, mock_session):
        with patch("bot.services.auth_service.admin_repo") as admin_repo, \
             patch("bot.services.auth_service.master_repo") as master_repo, \
             patch("bot.services.auth_service.owner_repo") as owner_repo:
            admin_repo.get_by_telegram_id = AsyncMock(return_value=None)
            master_repo.get_by_telegram_id = AsyncMock(return_value=None)
            owner_repo.get_by_telegram_id = AsyncMock(return_value=None)

            role, user_obj = await resolve_role(mock_session, 000000)
            assert role is None
            assert user_obj is None

    @pytest.mark.asyncio
    async def test_resolve_role_priority_admin_over_master(self, mock_session, fake_admin, fake_master):
        """Admin role takes priority even if user is also a master."""
        with patch("bot.services.auth_service.admin_repo") as admin_repo, \
             patch("bot.services.auth_service.master_repo") as master_repo, \
             patch("bot.services.auth_service.owner_repo"):
            admin_repo.get_by_telegram_id = AsyncMock(return_value=fake_admin)
            # master_repo should never be called
            role, user_obj = await resolve_role(mock_session, 999999)
            assert role == UserRole.ADMIN
            master_repo.get_by_telegram_id.assert_not_called()


class TestAuthenticateByPhone:
    @pytest.mark.asyncio
    async def test_authenticate_success(self, mock_session, fake_owner):
        with patch("bot.services.auth_service.owner_repo") as owner_repo, \
             patch("bot.services.auth_service.admin_repo") as admin_repo, \
             patch("bot.services.auth_service.master_repo") as master_repo:
            owner_repo.get_by_phone = AsyncMock(return_value=fake_owner)
            owner_repo.link_telegram_id = AsyncMock()
            admin_repo.get_by_telegram_id = AsyncMock(return_value=None)
            master_repo.get_by_telegram_id = AsyncMock(return_value=None)

            role, user_obj = await authenticate_by_phone(mock_session, "77001234567", 123456)
            assert role == UserRole.OWNER
            assert user_obj == fake_owner
            owner_repo.link_telegram_id.assert_called_once_with(mock_session, fake_owner.id, 123456)

    @pytest.mark.asyncio
    async def test_authenticate_not_found(self, mock_session):
        with patch("bot.services.auth_service.owner_repo") as owner_repo:
            owner_repo.get_by_phone = AsyncMock(return_value=None)

            role, user_obj = await authenticate_by_phone(mock_session, "70000000000", 123456)
            assert role is None
            assert user_obj is None

    @pytest.mark.asyncio
    async def test_authenticate_owner_is_also_admin(self, mock_session, fake_owner, fake_admin):
        with patch("bot.services.auth_service.owner_repo") as owner_repo, \
             patch("bot.services.auth_service.admin_repo") as admin_repo, \
             patch("bot.services.auth_service.master_repo"):
            owner_repo.get_by_phone = AsyncMock(return_value=fake_owner)
            owner_repo.link_telegram_id = AsyncMock()
            admin_repo.get_by_telegram_id = AsyncMock(return_value=fake_admin)

            role, user_obj = await authenticate_by_phone(mock_session, "77001234567", 123456)
            assert role == UserRole.ADMIN
            assert user_obj == fake_admin
