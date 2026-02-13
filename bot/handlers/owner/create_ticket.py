import logging

from aiogram import F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.owner import owner_router as router
from bot.states.create_ticket import CreateTicketState
from bot.callbacks.navigation_cb import OwnerMenuCB
from bot.callbacks.ticket_cb import (
    ComplexCB, CategoryCB, BlockCB, EntranceCB, SubCategoryCB,
    ConfirmCB, PhotoDoneCB, KeyCountCB, KeyTypeCB, GateCB,
    CameraInstructionCB, SkipCB, HasParkingCB,
)
from bot.keyboards.owner_kb import (
    complex_selector, category_selector, block_selector, entrance_selector,
    cctv_subtype_selector, intercom_subtype_selector, gate_selector,
    key_count_selector, key_type_selector, camera_instruction_buttons,
    easyviewer_instruction_buttons, photo_done_keyboard, confirm_keyboard,
    owner_main_menu,
)
from bot.utils.constants import (
    ResidentialComplex, TicketCategory,
    INSTRUCTION_HIK_CONNECT, INSTRUCTION_EASYVIEWER,
    CCTV_SUBTYPES, INTERCOM_SUBTYPES, ALASHA_GATES,
)
from bot.utils.formatting import format_ticket_confirmation
from bot.services import ticket_service, notification_service
from bot.services.text_service import get_text
from bot.db.repositories import owner_repo

logger = logging.getLogger(__name__)

MAX_TICKETS_PER_DAY = 10


@router.callback_query(OwnerMenuCB.filter(F.action == "create"))
async def start_create(callback: CallbackQuery, state: FSMContext, session: AsyncSession, user_obj=None, **kwargs):
    from bot.db.repositories import ticket_repo
    today_count = await ticket_repo.count_today_by_owner(session, callback.from_user.id)
    if today_count >= MAX_TICKETS_PER_DAY:
        text = await get_text(session, "create_limit_reached", count=today_count, limit=MAX_TICKETS_PER_DAY)
        await callback.answer(text, show_alert=True)
        return

    await state.clear()
    if user_obj:
        await state.update_data(
            client_full_name=user_obj.full_name,
            client_phone=user_obj.phone,
            client_telegram_id=callback.from_user.id,
        )
        rc = user_obj.residential_complex
        if rc:
            # Check if owner has multiple complexes
            complexes = [c.strip() for c in rc.split(",") if c.strip()]
            if len(complexes) == 1:
                # Single complex - proceed directly
                await state.update_data(residential_complex=complexes[0])
                await _after_complex_selected(callback.message, state, session, complexes[0])
                await callback.answer()
                return
            # Multiple complexes - show selector with only owner's complexes
            text = await get_text(session, "create_choose_complex")
            await callback.message.edit_text(text, reply_markup=complex_selector(filter_complexes=complexes))
            await state.set_state(CreateTicketState.choosing_complex)
            await callback.answer()
            return

    text = await get_text(session, "create_choose_complex")
    await callback.message.edit_text(text, reply_markup=complex_selector())
    await state.set_state(CreateTicketState.choosing_complex)
    await callback.answer()


@router.callback_query(CreateTicketState.choosing_complex, ComplexCB.filter())
async def process_complex(callback: CallbackQuery, callback_data: ComplexCB, state: FSMContext, session: AsyncSession, **kwargs):
    rc = callback_data.value
    await state.update_data(residential_complex=rc)
    await _after_complex_selected(callback.message, state, session, rc)
    await callback.answer()


async def _after_complex_selected(message: Message, state: FSMContext, session: AsyncSession, rc: str):
    if rc == ResidentialComplex.ALASHA:
        text = await get_text(session, "create_choose_entrance")
        await message.edit_text(text, reply_markup=entrance_selector())
        await state.set_state(CreateTicketState.choosing_entrance)
    else:
        text = await get_text(session, "create_choose_block")
        await message.edit_text(text, reply_markup=block_selector(rc))
        await state.set_state(CreateTicketState.choosing_block)


@router.callback_query(CreateTicketState.choosing_block, BlockCB.filter())
async def process_block(callback: CallbackQuery, callback_data: BlockCB, state: FSMContext, session: AsyncSession, **kwargs):
    await state.update_data(block=callback_data.value)
    text = await get_text(session, "create_enter_entrance")
    await callback.message.edit_text(text)
    await state.set_state(CreateTicketState.choosing_entrance)
    await callback.answer()


@router.callback_query(CreateTicketState.choosing_entrance, EntranceCB.filter())
async def process_entrance_button(callback: CallbackQuery, callback_data: EntranceCB, state: FSMContext, session: AsyncSession, **kwargs):
    await state.update_data(entrance=callback_data.value)
    text = await get_text(session, "create_enter_apartment")
    await callback.message.edit_text(text)
    await state.set_state(CreateTicketState.entering_apartment)
    await callback.answer()


@router.message(CreateTicketState.choosing_entrance, F.text)
async def process_entrance_text(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    await state.update_data(entrance=message.text.strip())
    text = await get_text(session, "create_enter_apartment")
    await message.answer(text)
    await state.set_state(CreateTicketState.entering_apartment)


@router.message(CreateTicketState.entering_apartment, F.text)
async def process_apartment(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    await state.update_data(apartment=message.text.strip())
    data = await state.get_data()
    rc = data["residential_complex"]
    text = await get_text(session, "create_choose_category")
    await message.answer(text, reply_markup=category_selector(rc))
    await state.set_state(CreateTicketState.choosing_category)


@router.callback_query(CreateTicketState.choosing_category, CategoryCB.filter())
async def process_category(callback: CallbackQuery, callback_data: CategoryCB, state: FSMContext, session: AsyncSession, **kwargs):
    cat = callback_data.value
    await state.update_data(category=cat)
    await callback.answer()
    await _route_to_category_fields(callback.message, state, session, cat)


async def _route_to_category_fields(message: Message, state: FSMContext, session: AsyncSession, cat: str):
    data = await state.get_data()
    rc = data.get("residential_complex", "")

    if cat == TicketCategory.CCTV:
        text = await get_text(session, "cctv_choose_subtype")
        await message.edit_text(text, reply_markup=cctv_subtype_selector())
        await state.set_state(CreateTicketState.choosing_cctv_subtype)

    elif cat == TicketCategory.FACE_ID:
        text = await get_text(session, "face_id_intro")
        await message.edit_text(text, reply_markup=photo_done_keyboard("face_id"))
        await state.set_state(CreateTicketState.entering_face_id_photos)

    elif cat == TicketCategory.CAR_PLATE:
        text = await get_text(session, "car_plate_intro")
        await message.edit_text(text)
        await state.set_state(CreateTicketState.entering_car_plate)

    elif cat == TicketCategory.CAMERA_ACCESS:
        if rc == ResidentialComplex.ALASHA:
            await message.edit_text(INSTRUCTION_HIK_CONNECT, reply_markup=camera_instruction_buttons())
        else:
            await message.edit_text(INSTRUCTION_EASYVIEWER, reply_markup=easyviewer_instruction_buttons())
        await state.set_state(CreateTicketState.viewing_camera_instruction)

    elif cat == TicketCategory.INTERCOM:
        text = await get_text(session, "intercom_intro")
        await message.edit_text(text, reply_markup=intercom_subtype_selector())
        await state.set_state(CreateTicketState.choosing_intercom_subtype)

    elif cat == TicketCategory.KEY_MAGNET:
        text = await get_text(session, "key_intro")
        await message.edit_text(text, reply_markup=key_count_selector())
        await state.set_state(CreateTicketState.choosing_key_count)

    else:
        text = await get_text(session, "other_intro")
        await message.edit_text(text)
        await state.set_state(CreateTicketState.entering_description)


@router.callback_query(CreateTicketState.choosing_cctv_subtype, SubCategoryCB.filter())
async def process_cctv_sub(callback: CallbackQuery, callback_data: SubCategoryCB, state: FSMContext, session: AsyncSession, **kwargs):
    idx = int(callback_data.value)
    sub_text = CCTV_SUBTYPES[idx] if idx < len(CCTV_SUBTYPES) else callback_data.value
    await state.update_data(sub_category=sub_text)
    text = await get_text(session, "create_enter_description")
    await callback.message.edit_text(text)
    await state.set_state(CreateTicketState.entering_description)
    await callback.answer()


@router.callback_query(CreateTicketState.choosing_intercom_subtype, SubCategoryCB.filter())
async def process_intercom_sub(callback: CallbackQuery, callback_data: SubCategoryCB, state: FSMContext, session: AsyncSession, **kwargs):
    idx = int(callback_data.value)
    sub_text = INTERCOM_SUBTYPES[idx] if idx < len(INTERCOM_SUBTYPES) else callback_data.value
    await state.update_data(sub_category=sub_text)
    text = await get_text(session, "create_enter_description")
    await callback.message.edit_text(text)
    await state.set_state(CreateTicketState.entering_description)
    await callback.answer()


@router.message(CreateTicketState.entering_face_id_photos, F.photo)
async def process_face_photo(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    data = await state.get_data()
    photos = data.get("face_id_photos", [])
    photos.append(message.photo[-1].file_id)
    await state.update_data(face_id_photos=photos)
    text = await get_text(session, "face_id_photo_added", count=len(photos))
    await message.answer(text, reply_markup=photo_done_keyboard("face_id"))


@router.callback_query(CreateTicketState.entering_face_id_photos, PhotoDoneCB.filter())
async def face_photos_done(callback: CallbackQuery, state: FSMContext, session: AsyncSession, **kwargs):
    text = await get_text(session, "face_id_describe")
    await callback.message.edit_text(text)
    await state.set_state(CreateTicketState.entering_description)
    await callback.answer()


@router.message(CreateTicketState.entering_car_plate, F.text)
async def process_car_plate(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    await state.update_data(car_plate=message.text.strip().upper())
    text = await get_text(session, "car_plate_choose_gate")
    await message.answer(text, reply_markup=gate_selector())
    await state.set_state(CreateTicketState.choosing_gate)


@router.callback_query(CreateTicketState.choosing_gate, GateCB.filter())
async def process_gate(callback: CallbackQuery, callback_data: GateCB, state: FSMContext, session: AsyncSession, **kwargs):
    idx = int(callback_data.value)
    gate_text = ALASHA_GATES[idx] if idx < len(ALASHA_GATES) else callback_data.value
    await state.update_data(car_gate=gate_text)

    btn_yes = await get_text(session, "btn_yes_parking")
    btn_no = await get_text(session, "btn_no_parking")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_yes, callback_data=HasParkingCB(value="yes").pack())],
        [InlineKeyboardButton(text=btn_no, callback_data=HasParkingCB(value="no").pack())],
    ])
    text = await get_text(session, "car_plate_has_parking")
    await callback.message.edit_text(text, reply_markup=kb)
    await state.set_state(CreateTicketState.choosing_has_parking)
    await callback.answer()


@router.callback_query(CreateTicketState.choosing_has_parking, HasParkingCB.filter())
async def process_has_parking(callback: CallbackQuery, callback_data: HasParkingCB, state: FSMContext, session: AsyncSession, **kwargs):
    has_parking = callback_data.value == "yes"
    await state.update_data(has_parking=has_parking)

    if has_parking:
        text = await get_text(session, "car_plate_upload_contract")
        await callback.message.edit_text(text)
        await state.set_state(CreateTicketState.uploading_parking_contract)
    else:
        text = await get_text(session, "car_plate_enter_reason")
        await callback.message.edit_text(text)
        await state.set_state(CreateTicketState.entering_parking_reason)
    await callback.answer()


@router.message(CreateTicketState.entering_parking_reason, F.text)
async def process_parking_reason(message: Message, state: FSMContext, **kwargs):
    await state.update_data(
        parking_reason=message.text.strip(),
        description=f"Причина: {message.text.strip()}",
    )
    data = await state.get_data()
    text = format_ticket_confirmation(data)
    await message.answer(text, reply_markup=confirm_keyboard())
    await state.set_state(CreateTicketState.confirming)


@router.message(CreateTicketState.uploading_parking_contract, F.photo)
async def process_parking_contract_photo(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    file_id = message.photo[-1].file_id
    await state.update_data(parking_contract_photo=file_id, description="Договор паркинга приложен")
    text = await get_text(session, "car_plate_enter_parking")
    await message.answer(text)
    await state.set_state(CreateTicketState.entering_parking)


@router.message(CreateTicketState.uploading_parking_contract, F.document)
async def process_parking_contract_doc(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    file_id = message.document.file_id
    await state.update_data(parking_contract_photo=file_id, description="Договор паркинга приложен")
    text = await get_text(session, "car_plate_enter_parking")
    await message.answer(text)
    await state.set_state(CreateTicketState.entering_parking)


@router.message(CreateTicketState.entering_parking, F.text)
async def process_parking(message: Message, state: FSMContext, **kwargs):
    await state.update_data(parking_number=message.text.strip())
    data = await state.get_data()
    text = format_ticket_confirmation(data)
    await message.answer(text, reply_markup=confirm_keyboard())
    await state.set_state(CreateTicketState.confirming)


@router.callback_query(CreateTicketState.viewing_camera_instruction, CameraInstructionCB.filter())
async def process_camera_instruction(callback: CallbackQuery, callback_data: CameraInstructionCB, state: FSMContext, session: AsyncSession, **kwargs):
    if callback_data.action == "back":
        await state.clear()
        text = await get_text(session, "menu_owner")
        await callback.message.edit_text(text, reply_markup=owner_main_menu())
        await callback.answer()
        return

    text = await get_text(session, "camera_enter_email")
    await callback.message.edit_text(text)
    await state.set_state(CreateTicketState.entering_camera_email)
    await callback.answer()


@router.message(CreateTicketState.entering_camera_email, F.text)
async def process_camera_email(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    await state.update_data(camera_access_email=message.text.strip())
    text = await get_text(session, "camera_enter_details")
    await message.answer(text)
    await state.set_state(CreateTicketState.entering_camera_details)


@router.message(CreateTicketState.entering_camera_details, F.text)
async def process_camera_details(message: Message, state: FSMContext, **kwargs):
    await state.update_data(
        camera_access_details=message.text.strip(),
        description=f"Доступ к камерам: {message.text.strip()}",
    )
    data = await state.get_data()
    text = format_ticket_confirmation(data)
    await message.answer(text, reply_markup=confirm_keyboard())
    await state.set_state(CreateTicketState.confirming)


@router.callback_query(CreateTicketState.choosing_key_count, KeyCountCB.filter())
async def process_key_count(callback: CallbackQuery, callback_data: KeyCountCB, state: FSMContext, session: AsyncSession, **kwargs):
    await state.update_data(key_count=callback_data.value)
    text = await get_text(session, "key_choose_type")
    await callback.message.edit_text(text, reply_markup=key_type_selector())
    await state.set_state(CreateTicketState.choosing_key_type)
    await callback.answer()


@router.callback_query(CreateTicketState.choosing_key_type, KeyTypeCB.filter())
async def process_key_type(callback: CallbackQuery, callback_data: KeyTypeCB, state: FSMContext, session: AsyncSession, **kwargs):
    display = "Новый (800 тг/шт)" if callback_data.value == "new" else "Перепрошивка"
    await state.update_data(key_type=display)
    text = await get_text(session, "key_add_comment")
    await callback.message.edit_text(text)
    await state.set_state(CreateTicketState.entering_description)
    await callback.answer()


@router.message(CreateTicketState.entering_description, F.text)
async def process_description(message: Message, state: FSMContext, **kwargs):
    await state.update_data(description=message.text.strip())
    data = await state.get_data()
    text = format_ticket_confirmation(data)
    await message.answer(text, reply_markup=confirm_keyboard())
    await state.set_state(CreateTicketState.confirming)


@router.message(CreateTicketState.uploading_photos, F.photo)
async def process_photo(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    data = await state.get_data()
    attachments = data.get("attachments", [])
    attachments.append(message.photo[-1].file_id)
    await state.update_data(attachments=attachments)
    text = await get_text(session, "photo_added", count=len(attachments))
    await message.answer(text, reply_markup=photo_done_keyboard("attachments"))


@router.message(CreateTicketState.uploading_photos, F.document)
async def process_document(message: Message, state: FSMContext, session: AsyncSession, **kwargs):
    data = await state.get_data()
    attachments = data.get("attachments", [])
    attachments.append(message.document.file_id)
    await state.update_data(attachments=attachments)
    text = await get_text(session, "file_added", count=len(attachments))
    await message.answer(text, reply_markup=photo_done_keyboard("attachments"))


@router.callback_query(CreateTicketState.uploading_photos, PhotoDoneCB.filter())
async def photos_done(callback: CallbackQuery, state: FSMContext, **kwargs):
    await _show_confirmation(callback.message, state)
    await callback.answer()


@router.callback_query(CreateTicketState.uploading_photos, SkipCB.filter())
async def skip_photos(callback: CallbackQuery, state: FSMContext, **kwargs):
    await _show_confirmation(callback.message, state)
    await callback.answer()


@router.callback_query(CreateTicketState.entering_face_id_photos, SkipCB.filter())
async def skip_face_photos(callback: CallbackQuery, state: FSMContext, session: AsyncSession, **kwargs):
    text = await get_text(session, "describe_request")
    await callback.message.edit_text(text)
    await state.set_state(CreateTicketState.entering_description)
    await callback.answer()


async def _show_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    text = format_ticket_confirmation(data)
    await message.edit_text(text, reply_markup=confirm_keyboard())
    await state.set_state(CreateTicketState.confirming)


@router.callback_query(CreateTicketState.confirming, ConfirmCB.filter())
async def process_confirm(
    callback: CallbackQuery,
    callback_data: ConfirmCB,
    state: FSMContext,
    session: AsyncSession,
    bot: Bot,
    **kwargs,
):
    from bot.utils.constants import TicketCategory, TicketStatus

    if callback_data.action == "cancel":
        await state.clear()
        text = await get_text(session, "create_cancelled")
        await callback.message.edit_text(text, reply_markup=owner_main_menu())
        await callback.answer()
        return

    data = await state.get_data()

    # Find all masters for this complex (for notifications only, NOT for assignment)
    from bot.db.repositories import master_repo
    masters = await master_repo.get_by_complex(session, data["residential_complex"])

    # Do NOT auto-assign master - master will accept the ticket themselves

    is_car_plate = data.get("category") == TicketCategory.CAR_PLATE
    if is_car_plate:
        data["status"] = TicketStatus.PENDING_APPROVAL

    try:
        ticket = await ticket_service.create_ticket(session, data)
        await session.commit()
    except Exception:
        logger.exception("Failed to create ticket for user %s", callback.from_user.id)
        text = await get_text(session, "error_generic")
        await callback.answer(text, show_alert=True)
        return

    await state.clear()

    if is_car_plate:
        text = await get_text(session, "create_submitted_approval", ticket_id=ticket.ticket_id)
    else:
        text = await get_text(session, "create_submitted", ticket_id=ticket.ticket_id)

    await callback.message.edit_text(text, reply_markup=owner_main_menu())

    # Notify ALL masters for this complex
    if masters:
        from bot.utils.formatting import format_ticket_card
        card = format_ticket_card(ticket)
        contract_photo = getattr(ticket, "parking_contract_photo", None)
        for master in masters:
            from bot.utils.language import get_user_language
            master_lang = get_user_language(master)
            if is_car_plate:
                await notification_service.notify_master_car_plate_approval(
                    bot, master.telegram_id, card, ticket.id, contract_photo=contract_photo,
                    recipient_lang=master_lang,
                )
            else:
                await notification_service.notify_master_new_ticket(
                    bot, master.telegram_id, card, ticket.id, recipient_lang=master_lang,
                )

    from bot.utils.formatting import format_ticket_card
    card = format_ticket_card(ticket)
    await notification_service.notify_admins_new_ticket(bot, session, card)

    toast = await get_text(session, "toast_ticket_submitted")
    await callback.answer(toast)
