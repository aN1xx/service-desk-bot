from aiogram import F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin import admin_router as router
from bot.callbacks.navigation_cb import AdminMenuCB
from bot.keyboards.admin_kb import (
    admin_main_menu, complex_filter_keyboard, master_filter_keyboard, date_filter_keyboard,
)
from bot.db.repositories import master_repo
from bot.services.text_service import get_text


@router.callback_query(AdminMenuCB.filter(F.action == "filter_complex"))
async def show_complex_filter(callback: CallbackQuery, session: AsyncSession, **kwargs):
    text = await get_text(session, "admin_choose_complex")
    await callback.message.edit_text(text, reply_markup=complex_filter_keyboard())
    await callback.answer()


@router.callback_query(AdminMenuCB.filter(F.action == "filter_master"))
async def show_master_filter(callback: CallbackQuery, session: AsyncSession, **kwargs):
    masters = await master_repo.list_all(session)
    text = await get_text(session, "admin_choose_master")
    await callback.message.edit_text(text, reply_markup=master_filter_keyboard(masters))
    await callback.answer()


@router.callback_query(AdminMenuCB.filter(F.action == "filter_date"))
async def show_date_filter(callback: CallbackQuery, session: AsyncSession, **kwargs):
    text = await get_text(session, "admin_choose_period")
    await callback.message.edit_text(text, reply_markup=date_filter_keyboard())
    await callback.answer()
