from aiogram import F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.owner import owner_router as router
from bot.callbacks.ticket_cb import TicketRateCB, RateCommentCB
from bot.states.rate_ticket import RateTicketState
from bot.services.ticket_service import rate_ticket
from bot.services.text_service import get_text
from bot.keyboards.owner_kb import owner_main_menu


@router.callback_query(TicketRateCB.filter())
async def process_rating(
    callback: CallbackQuery,
    callback_data: TicketRateCB,
    state: FSMContext,
    session: AsyncSession,
    **kwargs,
):
    stars = callback_data.stars
    ticket_pk = callback_data.ticket_pk
    await state.update_data(rating_ticket_pk=ticket_pk, rating_stars=stars)

    btn_add = await get_text(session, "btn_rate_add_comment")
    btn_skip = await get_text(session, "btn_rate_skip_comment")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_add, callback_data=RateCommentCB(action="add").pack())],
        [InlineKeyboardButton(text=btn_skip, callback_data=RateCommentCB(action="skip").pack())],
    ])
    text = await get_text(session, "rate_ask_comment", stars=stars)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(RateCommentCB.filter(F.action == "add"))
async def ask_comment(callback: CallbackQuery, state: FSMContext, session: AsyncSession, **kwargs):
    text = await get_text(session, "rate_comment_prompt")
    await callback.message.edit_text(text)
    await state.set_state(RateTicketState.waiting_comment)
    await callback.answer()


@router.message(RateTicketState.waiting_comment, F.text)
async def process_comment(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    data = await state.get_data()
    ticket_pk = data["rating_ticket_pk"]
    stars = data["rating_stars"]
    comment = message.text.strip()

    await rate_ticket(session, ticket_pk, stars, comment)
    await state.clear()

    text = await get_text(session, "rate_thanks")
    await message.answer(text, reply_markup=owner_main_menu())


@router.callback_query(RateCommentCB.filter(F.action == "skip"))
async def skip_comment(callback: CallbackQuery, state: FSMContext, session: AsyncSession, **kwargs):
    data = await state.get_data()
    ticket_pk = data["rating_ticket_pk"]
    stars = data["rating_stars"]

    await rate_ticket(session, ticket_pk, stars)
    await state.clear()

    text = await get_text(session, "rate_thanks")
    await callback.message.edit_text(text, reply_markup=owner_main_menu())
    await callback.answer()
