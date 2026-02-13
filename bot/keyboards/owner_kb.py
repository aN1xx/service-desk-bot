from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.callbacks.ticket_cb import (
    ComplexCB, CategoryCB, BlockCB, EntranceCB, SubCategoryCB,
    ConfirmCB, PhotoDoneCB, KeyCountCB, KeyTypeCB, GateCB,
    CameraInstructionCB, SkipCB, TicketViewCB, TicketRateCB,
)
from bot.callbacks.navigation_cb import PageCB, OwnerMenuCB, MenuCB, CancelCB
from bot.utils.constants import (
    ResidentialComplex, COMPLEX_DISPLAY, COMPLEX_CATEGORIES,
    CATEGORY_DISPLAY, STATUS_DISPLAY, COMPLEX_BLOCKS, ALASHA_ENTRANCES,
    CCTV_SUBTYPES, INTERCOM_SUBTYPES, ALASHA_GATES,
)


def owner_main_menu() -> InlineKeyboardMarkup:
    from bot.services.text_service import get_text_sync
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text_sync("btn_create_ticket"), callback_data=OwnerMenuCB(action="create").pack())],
        [InlineKeyboardButton(text=get_text_sync("btn_my_tickets"), callback_data=OwnerMenuCB(action="tickets").pack())],
        [InlineKeyboardButton(text=get_text_sync("btn_instructions"), callback_data=OwnerMenuCB(action="instructions").pack())],
        [InlineKeyboardButton(text="Тіл / Язык", callback_data=OwnerMenuCB(action="change_lang").pack())],
    ])


def complex_selector(filter_complexes: list[str] | None = None) -> InlineKeyboardMarkup:
    """
    Show complex selector.
    If filter_complexes is provided, only show those complexes.
    """
    buttons = []
    for rc in ResidentialComplex:
        # If filter provided, only show matching complexes
        if filter_complexes and rc.value not in filter_complexes:
            continue
        buttons.append([
            InlineKeyboardButton(
                text=COMPLEX_DISPLAY[rc],
                callback_data=ComplexCB(value=rc.value).pack(),
            )
        ])
    buttons.append([InlineKeyboardButton(text="Отмена", callback_data=CancelCB().pack())])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def category_selector(residential_complex: str) -> InlineKeyboardMarkup:
    try:
        rc = ResidentialComplex(residential_complex)
    except ValueError:
        rc = ResidentialComplex.ALASHA

    categories = COMPLEX_CATEGORIES[rc]
    buttons = []
    for cat in categories:
        buttons.append([
            InlineKeyboardButton(
                text=CATEGORY_DISPLAY[cat],
                callback_data=CategoryCB(value=cat.value).pack(),
            )
        ])
    buttons.append([InlineKeyboardButton(text="Отмена", callback_data=CancelCB().pack())])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def block_selector(residential_complex: str) -> InlineKeyboardMarkup:
    min_block, max_block = COMPLEX_BLOCKS.get(ResidentialComplex(residential_complex), (1, 10))
    rows = []
    row = []
    for i in range(min_block, max_block + 1):
        row.append(
            InlineKeyboardButton(text=str(i), callback_data=BlockCB(value=str(i)).pack())
        )
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Отмена", callback_data=CancelCB().pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def entrance_selector() -> InlineKeyboardMarkup:
    rows = []
    row = []
    for i in range(1, ALASHA_ENTRANCES + 1):
        row.append(
            InlineKeyboardButton(text=str(i), callback_data=EntranceCB(value=str(i)).pack())
        )
        if len(row) == 5:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="Отмена", callback_data=CancelCB().pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cctv_subtype_selector() -> InlineKeyboardMarkup:
    buttons = []
    for i, st in enumerate(CCTV_SUBTYPES):
        buttons.append([
            InlineKeyboardButton(text=st, callback_data=SubCategoryCB(value=str(i)).pack())
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def intercom_subtype_selector() -> InlineKeyboardMarkup:
    buttons = []
    for i, st in enumerate(INTERCOM_SUBTYPES):
        buttons.append([
            InlineKeyboardButton(text=st, callback_data=SubCategoryCB(value=str(i)).pack())
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def gate_selector() -> InlineKeyboardMarkup:
    buttons = []
    for i, g in enumerate(ALASHA_GATES):
        buttons.append([
            InlineKeyboardButton(text=g, callback_data=GateCB(value=str(i)).pack())
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def key_count_selector() -> InlineKeyboardMarkup:
    row = [
        InlineKeyboardButton(text=str(i), callback_data=KeyCountCB(value=i).pack())
        for i in range(1, 6)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[row])


def key_type_selector() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Новый (800 тг/шт)", callback_data=KeyTypeCB(value="new").pack())],
        [InlineKeyboardButton(text="Перепрошивка", callback_data=KeyTypeCB(value="reprogram").pack())],
    ])


def camera_instruction_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Я зарегистрировал(а) почту — продолжить",
            callback_data=CameraInstructionCB(action="continue").pack(),
        )],
        [InlineKeyboardButton(
            text="Назад в меню",
            callback_data=CameraInstructionCB(action="back").pack(),
        )],
    ])


def easyviewer_instruction_buttons() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Продолжить — получить доступ",
            callback_data=CameraInstructionCB(action="continue").pack(),
        )],
        [InlineKeyboardButton(
            text="Назад в меню",
            callback_data=CameraInstructionCB(action="back").pack(),
        )],
    ])


def photo_done_keyboard(kind: str = "attachments") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Готово", callback_data=PhotoDoneCB(kind=kind).pack())],
        [InlineKeyboardButton(text="Пропустить", callback_data=SkipCB(field=kind).pack())],
    ])


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отправить заявку", callback_data=ConfirmCB(action="send").pack())],
        [InlineKeyboardButton(text="Отмена", callback_data=ConfirmCB(action="cancel").pack())],
    ])


def rating_keyboard(ticket_pk: int) -> InlineKeyboardMarkup:
    row = [
        InlineKeyboardButton(
            text=f"{i}⭐",
            callback_data=TicketRateCB(ticket_pk=ticket_pk, stars=i).pack(),
        )
        for i in range(1, 6)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[row])


def ticket_list_keyboard(tickets: list, page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    for t in tickets:
        status_txt = STATUS_DISPLAY.get(t.status, t.status)
        buttons.append([
            InlineKeyboardButton(
                text=f"№{t.ticket_id} [{status_txt}]",
                callback_data=TicketViewCB(ticket_pk=t.id).pack(),
            )
        ])

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(
            text="◀ Назад",
            callback_data=PageCB(scope="owner_tickets", page=page - 1).pack(),
        ))
    if page < total_pages:
        nav.append(InlineKeyboardButton(
            text="Вперед ▶",
            callback_data=PageCB(scope="owner_tickets", page=page + 1).pack(),
        ))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(text="Главное меню", callback_data=MenuCB(action="owner").pack())])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
