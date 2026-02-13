from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.owner import owner_router as router
from bot.callbacks.ticket_cb import InstructionCB
from bot.callbacks.navigation_cb import PageCB, OwnerMenuCB, MenuCB
from bot.keyboards.owner_kb import owner_main_menu, ticket_list_keyboard
from bot.db.repositories import ticket_repo
from bot.services.text_service import get_text
from bot.utils.pagination import paginate, PER_PAGE
from bot.utils.constants import INSTRUCTION_HIK_CONNECT, INSTRUCTION_EASYVIEWER


@router.callback_query(OwnerMenuCB.filter(F.action == "tickets"))
async def my_tickets(callback: CallbackQuery, session: AsyncSession, **kwargs):
    await _show_tickets_page(callback, session, page=1)
    await callback.answer()


@router.callback_query(PageCB.filter(F.scope == "owner_tickets"))
async def paginate_tickets(callback: CallbackQuery, callback_data: PageCB, session: AsyncSession, **kwargs):
    await _show_tickets_page(callback, session, page=callback_data.page)
    await callback.answer()


async def _show_tickets_page(callback: CallbackQuery, session: AsyncSession, page: int):
    tg_id = callback.from_user.id
    total = await ticket_repo.count_by_owner(session, tg_id)

    if total == 0:
        text = await get_text(session, "owner_no_tickets")
        await callback.message.edit_text(text, reply_markup=owner_main_menu())
        return

    offset, limit, total_pages = paginate(total, page)
    tickets = await ticket_repo.list_by_owner(session, tg_id, limit=limit, offset=offset)

    text = await get_text(session, "owner_tickets_page", page=page, total=total_pages)
    await callback.message.edit_text(text, reply_markup=ticket_list_keyboard(tickets, page, total_pages))


@router.callback_query(OwnerMenuCB.filter(F.action == "instructions"))
async def show_instructions(callback: CallbackQuery, session: AsyncSession, **kwargs):
    btn_back = await get_text(session, "btn_back")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Hik-Connect (Alasha)", callback_data=InstructionCB(value="hik").pack())],
        [InlineKeyboardButton(text="EasyViewer (Terekti/Kemel/Jana)", callback_data=InstructionCB(value="easy").pack())],
        [InlineKeyboardButton(text=btn_back, callback_data=MenuCB(action="owner").pack())],
    ])
    text = await get_text(session, "choose_instruction")
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(InstructionCB.filter(F.value == "hik"))
async def show_hik_instruction(callback: CallbackQuery, session: AsyncSession, **kwargs):
    btn_back = await get_text(session, "btn_back")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_back, callback_data=OwnerMenuCB(action="instructions").pack())],
    ])
    await callback.message.edit_text(
        INSTRUCTION_HIK_CONNECT,
        reply_markup=kb,
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(InstructionCB.filter(F.value == "easy"))
async def show_easy_instruction(callback: CallbackQuery, session: AsyncSession, **kwargs):
    btn_back = await get_text(session, "btn_back")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_back, callback_data=OwnerMenuCB(action="instructions").pack())],
    ])
    await callback.message.edit_text(
        INSTRUCTION_EASYVIEWER,
        reply_markup=kb,
        disable_web_page_preview=True,
    )
    await callback.answer()
