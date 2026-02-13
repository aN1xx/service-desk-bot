"""Integration tests for repository layer with real SQLite database."""
import pytest
from datetime import datetime

from bot.db.models.owner import Owner
from bot.db.models.master import Master
from bot.db.models.admin import Admin
from bot.db.models.ticket import Ticket
from bot.db.models.ticket_history import TicketHistory
from bot.db.models.bot_text import BotText
from bot.db.repositories import owner_repo, master_repo, admin_repo, ticket_repo, bot_text_repo


class TestOwnerRepo:
    @pytest.mark.asyncio
    async def test_create_and_get_by_phone(self, db_session):
        owner = Owner(
            phone="77001234567",
            full_name="Test Owner",
            residential_complex="alasha",
            language="ru",
        )
        db_session.add(owner)
        await db_session.flush()

        result = await owner_repo.get_by_phone(db_session, "77001234567")
        assert result is not None
        assert result.full_name == "Test Owner"

    @pytest.mark.asyncio
    async def test_get_by_phone_not_found(self, db_session):
        result = await owner_repo.get_by_phone(db_session, "70000000000")
        assert result is None

    @pytest.mark.asyncio
    async def test_link_telegram_id(self, db_session):
        owner = Owner(
            phone="77009999999",
            full_name="Owner 2",
            residential_complex="terekti",
            language="ru",
        )
        db_session.add(owner)
        await db_session.flush()

        await owner_repo.link_telegram_id(db_session, owner.id, 555555)
        await db_session.flush()

        result = await owner_repo.get_by_telegram_id(db_session, 555555)
        assert result is not None
        assert result.phone == "77009999999"

    @pytest.mark.asyncio
    async def test_get_by_telegram_id_inactive(self, db_session):
        owner = Owner(
            phone="77008888888",
            full_name="Inactive Owner",
            residential_complex="alasha",
            telegram_id=777777,
            is_active=False,
            language="ru",
        )
        db_session.add(owner)
        await db_session.flush()

        result = await owner_repo.get_by_telegram_id(db_session, 777777)
        assert result is None


class TestMasterRepo:
    @pytest.mark.asyncio
    async def test_create_and_get_by_telegram_id(self, db_session):
        master = Master(
            telegram_id=654321,
            full_name="Test Master",
            residential_complex="alasha,terekti",
            language="ru",
        )
        db_session.add(master)
        await db_session.flush()

        result = await master_repo.get_by_telegram_id(db_session, 654321)
        assert result is not None
        assert result.full_name == "Test Master"

    @pytest.mark.asyncio
    async def test_get_by_complex(self, db_session):
        master = Master(
            telegram_id=111111,
            full_name="Alasha Master",
            residential_complex="alasha,terekti",
            language="ru",
        )
        db_session.add(master)
        await db_session.flush()

        results = await master_repo.get_by_complex(db_session, "alasha")
        assert len(results) >= 1
        assert any(m.full_name == "Alasha Master" for m in results)

    @pytest.mark.asyncio
    async def test_get_all_active(self, db_session):
        m1 = Master(telegram_id=222221, full_name="Active", residential_complex="alasha", language="ru")
        m2 = Master(telegram_id=222222, full_name="Inactive", residential_complex="alasha", is_active=False, language="ru")
        db_session.add_all([m1, m2])
        await db_session.flush()

        results = await master_repo.get_all_active(db_session)
        names = [m.full_name for m in results]
        assert "Active" in names
        assert "Inactive" not in names


class TestAdminRepo:
    @pytest.mark.asyncio
    async def test_create_and_get_all(self, db_session):
        admin = Admin(telegram_id=999999, full_name="Test Admin", language="ru")
        db_session.add(admin)
        await db_session.flush()

        results = await admin_repo.get_all(db_session)
        assert len(results) >= 1
        assert any(a.full_name == "Test Admin" for a in results)

    @pytest.mark.asyncio
    async def test_get_by_telegram_id(self, db_session):
        admin = Admin(telegram_id=888888, full_name="Admin 2", language="kk")
        db_session.add(admin)
        await db_session.flush()

        result = await admin_repo.get_by_telegram_id(db_session, 888888)
        assert result is not None
        assert result.language == "kk"


class TestTicketRepo:
    async def _create_test_ticket(self, db_session, **overrides):
        defaults = dict(
            ticket_id="QSS-20250101-0001",
            client_telegram_id=123456,
            client_phone="77001234567",
            client_full_name="Test Owner",
            residential_complex="alasha",
            category="cctv",
            description="Test ticket",
            status="new",
        )
        defaults.update(overrides)
        return await ticket_repo.create(db_session, **defaults)

    @pytest.mark.asyncio
    async def test_create_and_get_by_id(self, db_session):
        ticket = await self._create_test_ticket(db_session)
        await db_session.flush()

        result = await ticket_repo.get_by_id(db_session, ticket.id)
        assert result is not None
        assert result.ticket_id == "QSS-20250101-0001"
        assert result.category == "cctv"

    @pytest.mark.asyncio
    async def test_update_status(self, db_session):
        ticket = await self._create_test_ticket(db_session)
        await db_session.flush()

        await ticket_repo.update_status(db_session, ticket.id, "in_progress")
        await db_session.flush()

        result = await ticket_repo.get_by_id(db_session, ticket.id)
        assert result.status == "in_progress"

    @pytest.mark.asyncio
    async def test_update_status_completed_sets_timestamp(self, db_session):
        ticket = await self._create_test_ticket(db_session)
        await db_session.flush()

        await ticket_repo.update_status(db_session, ticket.id, "completed")
        await db_session.flush()

        result = await ticket_repo.get_by_id(db_session, ticket.id)
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_add_and_get_history(self, db_session):
        ticket = await self._create_test_ticket(db_session)
        await db_session.flush()

        await ticket_repo.add_history(
            db_session,
            ticket_pk=ticket.id,
            old_status=None,
            new_status="new",
            changed_by_id=123456,
            changed_by_role="owner",
            comment="Created",
        )
        await db_session.flush()

        history = await ticket_repo.get_history(db_session, ticket.id)
        assert len(history) == 1
        assert history[0].new_status == "new"
        assert history[0].comment == "Created"

    @pytest.mark.asyncio
    async def test_set_rating(self, db_session):
        ticket = await self._create_test_ticket(db_session)
        await db_session.flush()

        await ticket_repo.set_rating(db_session, ticket.id, 5, "Great!")
        await db_session.flush()

        result = await ticket_repo.get_by_id(db_session, ticket.id)
        assert result.rating == 5
        assert result.rating_comment == "Great!"
        assert result.status == "closed"

    @pytest.mark.asyncio
    async def test_reassign_master(self, db_session):
        master = Master(
            telegram_id=654321,
            full_name="Master",
            residential_complex="alasha",
            language="ru",
        )
        db_session.add(master)
        await db_session.flush()

        ticket = await self._create_test_ticket(db_session)
        await db_session.flush()

        await ticket_repo.reassign_master(db_session, ticket.id, master.id)
        await db_session.flush()

        result = await ticket_repo.get_by_id(db_session, ticket.id)
        assert result.assigned_master_id == master.id

    @pytest.mark.asyncio
    async def test_generate_ticket_id_format(self, db_session):
        ticket_id = await ticket_repo.generate_ticket_id(db_session)
        assert ticket_id.startswith("QSS-")
        parts = ticket_id.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 4  # NNNN

    @pytest.mark.asyncio
    async def test_list_by_owner(self, db_session):
        await self._create_test_ticket(db_session, ticket_id="QSS-T-0001")
        await self._create_test_ticket(db_session, ticket_id="QSS-T-0002")
        await db_session.flush()

        results = await ticket_repo.list_by_owner(db_session, 123456)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_count_by_owner(self, db_session):
        await self._create_test_ticket(db_session, ticket_id="QSS-C-0001")
        await self._create_test_ticket(db_session, ticket_id="QSS-C-0002", client_telegram_id=999)
        await db_session.flush()

        count = await ticket_repo.count_by_owner(db_session, 123456)
        assert count == 1

    @pytest.mark.asyncio
    async def test_list_filtered_by_status(self, db_session):
        await self._create_test_ticket(db_session, ticket_id="QSS-F-0001", status="new")
        await self._create_test_ticket(db_session, ticket_id="QSS-F-0002", status="completed")
        await db_session.flush()

        results = await ticket_repo.list_filtered(db_session, status="new")
        assert all(t.status == "new" for t in results)

    @pytest.mark.asyncio
    async def test_list_filtered_by_complex(self, db_session):
        await self._create_test_ticket(db_session, ticket_id="QSS-X-0001", residential_complex="alasha")
        await self._create_test_ticket(db_session, ticket_id="QSS-X-0002", residential_complex="terekti")
        await db_session.flush()

        results = await ticket_repo.list_filtered(db_session, residential_complex="alasha")
        assert all(t.residential_complex == "alasha" for t in results)


class TestBotTextRepo:
    @pytest.mark.asyncio
    async def test_upsert_and_get(self, db_session):
        await bot_text_repo.upsert(db_session, "test_key", "Test value", "ru", "Test desc")
        await db_session.flush()

        result = await bot_text_repo.get_by_key(db_session, "test_key", "ru")
        assert result == "Test value"

    @pytest.mark.asyncio
    async def test_upsert_updates_existing(self, db_session):
        await bot_text_repo.upsert(db_session, "upd_key", "Old value", "ru")
        await db_session.flush()
        await bot_text_repo.upsert(db_session, "upd_key", "New value", "ru")
        await db_session.flush()

        result = await bot_text_repo.get_by_key(db_session, "upd_key", "ru")
        assert result == "New value"

    @pytest.mark.asyncio
    async def test_get_all_as_dict(self, db_session):
        await bot_text_repo.upsert(db_session, "dict_key", "RU val", "ru")
        await bot_text_repo.upsert(db_session, "dict_key", "KK val", "kk")
        await db_session.flush()

        result = await bot_text_repo.get_all_as_dict(db_session)
        assert "dict_key" in result
        assert result["dict_key"]["ru"] == "RU val"
        assert result["dict_key"]["kk"] == "KK val"

    @pytest.mark.asyncio
    async def test_get_by_key_not_found(self, db_session):
        result = await bot_text_repo.get_by_key(db_session, "nonexistent", "ru")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_value(self, db_session):
        text_obj = await bot_text_repo.upsert(db_session, "val_key", "Original", "ru")
        await db_session.flush()

        success = await bot_text_repo.update_value(db_session, text_obj.id, "Updated")
        assert success is True

        result = await bot_text_repo.get_by_key(db_session, "val_key", "ru")
        assert result == "Updated"
