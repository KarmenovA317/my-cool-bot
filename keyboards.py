"""
keyboards.py
Все клавиатуры бота: инлайн-кнопки калькулятора и reply-кнопки главного меню.
"""
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from config import GLASS_PRICES, PROFILE_PRICES

BTN_CALC = "🧮 Рассчитать стоимость"
BTN_QUESTION = "ℹ️ Задать вопрос"


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_CALC)],
            [KeyboardButton(text=BTN_QUESTION)],
        ],
        resize_keyboard=True,
    )


def profile_type_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=data["label"], callback_data=f"profile:{key}")]
        for key, data in PROFILE_PRICES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def glass_type_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=data["label"], callback_data=f"glass:{key}")]
        for key, data in GLASS_PRICES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_order_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Оставить заявку", callback_data="leave_request")],
            [InlineKeyboardButton(text="🔄 Рассчитать заново", callback_data="restart_calc")],
        ]
    )


def contact_request_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )