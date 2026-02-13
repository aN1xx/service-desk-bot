from datetime import date, timedelta

from aiogram import F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin import admin_router as router
from bot.callbacks.admin_cb import AdminFilterCB
from bot.callbacks.navigation_cb import PageCB, AdminMenuCB
from bot.keyboards.admin_kb import admin_ticket_list, admin_main_menu
from bot.db.repositories import ticket_repo
from bot.services.text_service import get_text
from bot.utils.pagination import paginate


@router.callback_query(AdminMenuCB.filter(F.action == "all"))
async def admin_all_tickets(callback: CallbackQuery, session: AsyncSession, state: FSMContext, **kwargs):
    await state.update_data(
        admin_filter_status=None,
        admin_filter_complex=None,
        admin_filter_master=None,
        admin_filter_date=None,
    )
    await _show_admin_tickets(callback, session, state, page=1)


@router.callback_query(AdminFilterCB.filter())
async def admin_filter(callback: CallbackQuery, callback_data: AdminFilterCB, session: AsyncSession, state: FSMContext, **kwargs):
    if callback_data.filter_type == "status":
        await state.update_data(
            admin_filter_status=callback_data.value,
            admin_filter_complex=None,
            admin_filter_master=None,
            admin_filter_date=None,
        )
    elif callback_data.filter_type == "complex":
        await state.update_data(admin_filter_complex=callback_data.value)
    elif callback_data.filter_type == "master":
        await state.update_data(admin_filter_master=int(callback_data.value))
    elif callback_data.filter_type == "date":
        await state.update_data(admin_filter_date=callback_data.value)
    await _show_admin_tickets(callback, session, state, page=1)


@router.callback_query(PageCB.filter(F.scope == "admin_tickets"))
async def paginate_admin_tickets(callback: CallbackQuery, callback_data: PageCB, session: AsyncSession, state: FSMContext, **kwargs):
    await _show_admin_tickets(callback, session, state, page=callback_data.page)


async def _show_admin_tickets(callback: CallbackQuery, session: AsyncSession, state: FSMContext, page: int):
    data = await state.get_data()
    status = data.get("admin_filter_status")
    residential_complex = data.get("admin_filter_complex")
    master_id = data.get("admin_filter_master")
    date_filter = data.get("admin_filter_date")

    date_from = None
    date_to = None
    today = date.today()
    if date_filter == "today":
        date_from = today
        date_to = today
    elif date_filter == "week":
        date_from = today - timedelta(days=7)
        date_to = today
    elif date_filter == "month":
        date_from = today - timedelta(days=30)
        date_to = today

    total = await ticket_repo.count_filtered(
        session,
        status=status,
        residential_complex=residential_complex,
        master_id=master_id,
        date_from=date_from,
        date_to=date_to,
    )

    if total == 0:
        text = await get_text(session, "admin_no_tickets")
        await callback.message.edit_text(text, reply_markup=admin_main_menu())
        await callback.answer()
        return

    offset, limit, total_pages = paginate(total, page)
    tickets = await ticket_repo.list_filtered(
        session,
        status=status,
        residential_complex=residential_complex,
        master_id=master_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )

    filter_desc = ""
    if status:
        filter_desc += f" (статус: {status})"
    if residential_complex:
        filter_desc += f" (ЖК: {residential_complex})"
    if master_id:
        filter_desc += " (мастер)"
    if date_filter:
        date_labels = {"today": "сегодня", "week": "неделя", "month": "месяц"}
        filter_desc += f" ({date_labels.get(date_filter, date_filter)})"

    text = await get_text(session, "admin_tickets_page", filter=filter_desc, page=page, total=total_pages)
    await callback.message.edit_text(text, reply_markup=admin_ticket_list(tickets, page, total_pages))
    await callback.answer()
