from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from bot.callbacks.navigation_cb import BackCB, CancelCB, LanguageCB
from bot.services.text_service import get_text_sync


def contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=get_text_sync("btn_send_contact"), request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def language_selector() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Русский 🇷🇺", callback_data=LanguageCB(lang="ru").pack())],
        [InlineKeyboardButton(text="Қазақша 🇰🇿", callback_data=LanguageCB(lang="kk").pack())],
    ])


def cancel_inline() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=get_text_sync("btn_cancel"), callback_data=CancelCB().pack())]
        ]
    )


def back_button(target: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=get_text_sync("btn_back"), callback_data=BackCB(target=target).pack()
    )


def skip_button(text: str = "Пропустить", callback_data: str = "skip") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=callback_data)
