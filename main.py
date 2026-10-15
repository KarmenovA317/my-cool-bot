"""
main.py
Точка входа Telegram-бота компании "Astana Shyntas".

Функционал:
- Умный консультант на Gemini для свободных вопросов (ai_handler.py).
- Пошаговый калькулятор стоимости на aiogram.fsm (State Machine).
- Приём контакта клиента, запись лида в Google Таблицу (sheets_db.py)
  и мгновенное уведомление менеджеру в личные сообщения.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message

import ai_handler
import sheets_db
from config import (
    BOT_TOKEN,
    FITTINGS_PRICE,
    GLASS_PRICES,
    INSTALLATION_MARKUP,
    MANAGER_CHAT_ID,
    MAX_DIMENSION_M,
    MIN_DIMENSION_M,
    PROFILE_PRICES,
)
from keyboards import (
    BTN_CALC,
    BTN_QUESTION,
    confirm_order_kb,
    contact_request_kb,
    glass_type_kb,
    main_menu_kb,
    profile_type_kb,
)
from states import OrderForm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

router = Router()


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def calculate_price(profile_key: str, glass_key: str, width: float, height: float) -> dict:
    """Считает стоимость конструкции по формулам из ТЗ."""
    area = width * height
    profile_price = PROFILE_PRICES[profile_key]["price"]
    glass_price = GLASS_PRICES[glass_key]["price"]

    materials_cost = (area * profile_price) + (area * glass_price) + FITTINGS_PRICE
    total_cost = materials_cost * (1 + INSTALLATION_MARKUP)

    return {
        "area": round(area, 2),
        "materials_cost": round(materials_cost),
        "total_cost": round(total_cost),
    }


def parse_dimension(text: str) -> float | None:
    """Парсит введённое пользователем число (ширину/высоту), допуская запятую."""
    normalized = text.strip().replace(",", ".")
    try:
        value = float(normalized)
    except ValueError:
        return None
    if not (MIN_DIMENSION_M <= value <= MAX_DIMENSION_M):
        return None
    return value


def format_tenge(amount: int) -> str:
    return f"{amount:,} тг".replace(",", " ")


# ---------------------------------------------------------------------------
# Базовые команды и главное меню
# ---------------------------------------------------------------------------

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Здравствуйте! 👋 Я бот-консультант компании <b>Astana Shyntas</b>.\n\n"
        "Мы производим и монтируем алюминиевые окна, двери, витражи и фасады "
        "в Астане.\n\n"
        "Я могу:\n"
        "🧮 рассчитать предварительную стоимость вашей конструкции;\n"
        "ℹ️ ответить на вопросы про алюминиевые конструкции.\n\n"
        "Выберите действие или просто напишите вопрос.",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("calc"))
@router.message(F.text == BTN_CALC)
async def start_calculator(message: Message, state: FSMContext) -> None:
    await state.set_state(OrderForm.choosing_profile)
    await message.answer("Выберите тип профиля:", reply_markup=profile_type_kb())


@router.message(F.text == BTN_QUESTION)
async def prompt_question(message: Message) -> None:
    await message.answer("Напишите ваш вопрос про алюминиевые конструкции — я отвечу 🙂")


# ---------------------------------------------------------------------------
# FSM: калькулятор стоимости
# ---------------------------------------------------------------------------

@router.callback_query(OrderForm.choosing_profile, F.data.startswith("profile:"))
async def process_profile(callback: CallbackQuery, state: FSMContext) -> None:
    profile_key = callback.data.split(":", 1)[1]
    await state.update_data(profile_key=profile_key)
    await state.set_state(OrderForm.choosing_glass)

    await callback.message.edit_text(
        f"Профиль: <b>{PROFILE_PRICES[profile_key]['label']}</b>\n\n"
        "Теперь выберите тип остекления:",
        reply_markup=glass_type_kb(),
    )
    await callback.answer()


@router.callback_query(OrderForm.choosing_glass, F.data.startswith("glass:"))
async def process_glass(callback: CallbackQuery, state: FSMContext) -> None:
    glass_key = callback.data.split(":", 1)[1]
    await state.update_data(glass_key=glass_key)
    await state.set_state(OrderForm.entering_width)

    await callback.message.edit_text(
        f"Остекление: <b>{GLASS_PRICES[glass_key]['label']}</b>\n\n"
        "Введите ширину конструкции в метрах (например: 1.5):"
    )
    await callback.answer()


@router.message(OrderForm.entering_width)
async def process_width(message: Message, state: FSMContext) -> None:
    width = parse_dimension(message.text or "")
    if width is None:
        await message.answer(
            f"Некорректное значение. Введите ширину в метрах "
            f"(от {MIN_DIMENSION_M} до {MAX_DIMENSION_M}), например: 1.5"
        )
        return

    await state.update_data(width=width)
    await state.set_state(OrderForm.entering_height)
    await message.answer("Теперь введите высоту конструкции в метрах (например: 1.8):")


@router.message(OrderForm.entering_height)
async def process_height(message: Message, state: FSMContext) -> None:
    height = parse_dimension(message.text or "")
    if height is None:
        await message.answer(
            f"Некорректное значение. Введите высоту в метрах "
            f"(от {MIN_DIMENSION_M} до {MAX_DIMENSION_M}), например: 1.8"
        )
        return

    data = await state.update_data(height=height)
    result = calculate_price(data["profile_key"], data["glass_key"], data["width"], height)
    await state.update_data(area=result["area"], total_cost=result["total_cost"])

    profile_label = PROFILE_PRICES[data["profile_key"]]["label"]
    glass_label = GLASS_PRICES[data["glass_key"]]["label"]

    await message.answer(
        "📐 <b>Предварительный расчёт</b>\n\n"
        f"Профиль: {profile_label}\n"
        f"Остекление: {glass_label}\n"
        f"Габариты: {data['width']} × {height} м (площадь {result['area']} м²)\n\n"
        f"💰 Предварительная стоимость: <b>{format_tenge(result['total_cost'])}</b>\n\n"
        "Это ориентировочная сумма без учёта доп. опций и выезда замерщика. "
        "Хотите оставить заявку, чтобы менеджер уточнил детали и зафиксировал цену?",
        reply_markup=confirm_order_kb(),
    )
    # Сбрасываем только состояние (ждём нажатия кнопки), данные остаются в FSM-контексте
    await state.set_state(None)


@router.callback_query(F.data == "restart_calc")
async def restart_calc(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OrderForm.choosing_profile)
    await callback.message.edit_text("Начнём заново. Выберите тип профиля:", reply_markup=profile_type_kb())
    await callback.answer()


@router.callback_query(F.data == "leave_request")
async def leave_request(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(OrderForm.entering_name)
    await callback.message.answer("Отлично! Как к вам обращаться? Напишите, пожалуйста, ваше имя.")
    await callback.answer()


@router.message(OrderForm.entering_name)
async def process_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Пожалуйста, напишите ваше имя текстом.")
        return

    await state.update_data(name=name)
    await state.set_state(OrderForm.entering_phone)
    await message.answer(
        "Спасибо! Теперь отправьте ваш номер телефона, нажав на кнопку ниже 👇",
        reply_markup=contact_request_kb(),
    )


@router.message(OrderForm.entering_phone, F.contact)
async def process_phone(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    phone = message.contact.phone_number

    profile_label = PROFILE_PRICES[data["profile_key"]]["label"]
    glass_label = GLASS_PRICES[data["glass_key"]]["label"]
    dimensions = f"{data['width']}x{data['height']}"
    total_cost_str = format_tenge(data["total_cost"])

    lead_text = (
        "🆕 <b>Новая заявка с Telegram-бота</b>\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {phone}\n"
        f"🧱 Профиль: {profile_label}\n"
        f"🪟 Остекление: {glass_label}\n"
        f"📐 Габариты (ШхВ): {dimensions} м\n"
        f"💰 Предварительная стоимость: {total_cost_str}"
    )

    try:
        await sheets_db.add_lead(
            name=data["name"],
            phone=phone,
            profile_type=profile_label,
            glass_type=glass_label,
            dimensions=dimensions,
            total_cost=total_cost_str,
        )
    except Exception:
        logger.exception("Заявка не записана в Google Sheets, но клиенту и менеджеру всё равно отвечаем")

    if MANAGER_CHAT_ID:
        try:
            await bot.send_message(MANAGER_CHAT_ID, lead_text)
        except Exception:
            logger.exception("Не удалось отправить уведомление менеджеру")
    else:
        logger.warning("MANAGER_CHAT_ID не задан — уведомление менеджеру не отправлено")

    await message.answer(
        "Спасибо! Ваша заявка принята ✅\nНаш менеджер свяжется с вами в ближайшее время.",
        reply_markup=main_menu_kb(),
    )
    await state.clear()


@router.message(OrderForm.entering_phone)
async def process_phone_invalid(message: Message) -> None:
    await message.answer("Пожалуйста, воспользуйтесь кнопкой ниже, чтобы отправить номер телефона.")


# ---------------------------------------------------------------------------
# Свободные вопросы -> Gemini (срабатывает, когда пользователь не в сценарии FSM)
# ---------------------------------------------------------------------------

@router.message(StateFilter(None))
async def handle_free_text(message: Message, bot: Bot) -> None:
    if not message.text:
        return
    await bot.send_chat_action(message.chat.id, "typing")
    answer = await ai_handler.ask_gemini(message.text)
    await message.answer(answer)


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------

async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Бот Astana Shyntas запущен, начинаем polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())