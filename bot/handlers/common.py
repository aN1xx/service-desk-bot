import logging

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.common import contact_keyboard, language_selector
from bot.keyboards.owner_kb import owner_main_menu
from bot.keyboards.master_kb import master_main_menu
from bot.keyboards.admin_kb import admin_main_menu
from bot.services.auth_service import authenticate_by_phone
from bot.services.text_service import get_text
from bot.states.auth import AuthState
from bot.utils.constants import UserRole
from bot.utils.language import current_language
from bot.callbacks.navigation_cb import CancelCB, MenuCB, LanguageCB, OwnerMenuCB, MasterMenuCB, AdminMenuCB

logger = logging.getLogger(__name__)
router = Router(name="common")


def _normalize_phone(phone: str) -> str:
    """Strip everything except digits, ensure leading 7 for KZ numbers."""
    digits = "".join(c for c in phone if c.isdigit())
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    if digits.startswith("+"):
        digits = digits[1:]
    return digits


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession, user_role: str | None = None, **kwargs):
    await state.clear()
    if user_role:
        await _show_menu(message, session, user_role)
        return

    # Show language selection first
    await message.answer(
        "Тілді таңдаңыз / Выберите язык:",
        reply_markup=language_selector(),
    )
    await state.set_state(AuthState.choosing_language)


@router.callback_query(AuthState.choosing_language, LanguageCB.filter())
async def process_language_choice(
    callback: CallbackQuery, callback_data: LanguageCB, state: FSMContext, session: AsyncSession, **kwargs
):
    lang = callback_data.lang
    await state.update_data(chosen_language=lang)

    # Set language for this request
    current_language.set(lang)

    text = await get_text(session, "start_welcome")
    await callback.message.edit_text(text)
    await callback.message.answer(
        await get_text(session, "auth_send_contact"),
        reply_markup=contact_keyboard(),
    )
    await state.set_state(AuthState.waiting_contact)
    await callback.answer()


@router.message(AuthState.waiting_contact, F.contact)
async def process_contact(
    message: Message, state: FSMContext, session: AsyncSession, **kwargs
):
    phone = _normalize_phone(message.contact.phone_number)
    telegram_id = message.from_user.id

    role, user_obj = await authenticate_by_phone(session, phone, telegram_id)

    if role:
        # Save chosen language to user object
        data = await state.get_data()
        lang = data.get("chosen_language", "ru")
        if hasattr(user_obj, "language"):
            user_obj.language = lang
        current_language.set(lang)

        await state.clear()
        text = await get_text(session, "auth_success", full_name=user_obj.full_name)
        await message.answer(text, reply_markup=ReplyKeyboardRemove())
        await _show_menu(message, session, role)
    else:
        text = await get_text(session, "auth_failed")
        await message.answer(text, reply_markup=ReplyKeyboardRemove())
        await state.clear()


@router.message(AuthState.waiting_contact)
async def wrong_contact(message: Message, session: AsyncSession, **kwargs):
    text = await get_text(session, "auth_send_contact")
    await message.answer(text, reply_markup=contact_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message, session: AsyncSession, **kwargs):
    text = await get_text(session, "help_text")
    await message.answer(text)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, session: AsyncSession, user_role: str | None = None, **kwargs):
    current = await state.get_state()
    if current:
        await state.clear()
        text = await get_text(session, "action_cancelled")
        await message.answer(text)
    else:
        text = await get_text(session, "no_active_action")
        await message.answer(text)
    if user_role:
        await _show_menu(message, session, user_role)


@router.callback_query(CancelCB.filter())
async def cancel_action_cb(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user_role: str | None = None, **kwargs):
    await state.clear()
    text = await get_text(session, "action_cancelled")
    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(MenuCB.filter())
async def menu_cb(callback: CallbackQuery, callback_data: MenuCB, session: AsyncSession, **kwargs):
    """Universal menu callback for all roles."""
    action = callback_data.action
    if action == "owner":
        text = await get_text(session, "menu_owner")
        await callback.message.edit_text(text, reply_markup=owner_main_menu())
    elif action == "master":
        text = await get_text(session, "menu_master")
        await callback.message.edit_text(text, reply_markup=master_main_menu())
    elif action == "admin":
        text = await get_text(session, "menu_admin")
        await callback.message.edit_text(text, reply_markup=admin_main_menu())
    await callback.answer()


# --- Language change from menu ---

@router.callback_query(OwnerMenuCB.filter(F.action == "change_lang"))
@router.callback_query(MasterMenuCB.filter(F.action == "change_lang"))
@router.callback_query(AdminMenuCB.filter(F.action == "change_lang"))
async def show_language_picker(callback: CallbackQuery, session: AsyncSession, **kwargs):
    await callback.message.edit_text(
        "Тілді таңдаңыз / Выберите язык:",
        reply_markup=language_selector(),
    )
    await callback.answer()


@router.callback_query(LanguageCB.filter())
async def change_language_cb(
    callback: CallbackQuery, callback_data: LanguageCB, session: AsyncSession,
    user_role: str | None = None, user_obj=None, **kwargs
):
    lang = callback_data.lang
    current_language.set(lang)

    # Save language to DB
    if user_obj and hasattr(user_obj, "language"):
        user_obj.language = lang

    # Show updated menu
    if user_role == UserRole.ADMIN:
        text = await get_text(session, "menu_admin")
        await callback.message.edit_text(text, reply_markup=admin_main_menu())
    elif user_role == UserRole.MASTER:
        text = await get_text(session, "menu_master")
        await callback.message.edit_text(text, reply_markup=master_main_menu())
    else:
        text = await get_text(session, "menu_owner")
        await callback.message.edit_text(text, reply_markup=owner_main_menu())
    await callback.answer()


async def _show_menu(message: Message, session: AsyncSession, role: str):
    if role == UserRole.ADMIN:
        text = await get_text(session, "menu_admin")
        await message.answer(text, reply_markup=admin_main_menu())
    elif role == UserRole.MASTER:
        text = await get_text(session, "menu_master")
        await message.answer(text, reply_markup=master_main_menu())
    else:
        text = await get_text(session, "menu_owner")
        await message.answer(text, reply_markup=owner_main_menu())
