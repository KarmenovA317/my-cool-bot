"""
config.py
Загрузка переменных окружения и справочник цен компании "Astana Shyntas".
"""
import os

from dotenv import load_dotenv

load_dotenv()

# --- Telegram / Gemini / Google ---
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MANAGER_CHAT_ID: int = int(os.getenv("MANAGER_CHAT_ID", "0"))

GOOGLE_CREDENTIALS_FILE: str = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_SHEET_WORKSHEET: str = os.getenv("GOOGLE_SHEET_WORKSHEET", "Лиды")

# --- Прайс-лист (тенге за м²), заложен по ТЗ ---
PROFILE_PRICES = {
    "cold": {"label": "Холодный алюминий", "price": 28_000},
    "warm": {"label": "Тёплый алюминий", "price": 48_000},
}

GLASS_PRICES = {
    "standard": {"label": "Стандартное остекление", "price": 10_000},
    "double": {"label": "Двухкамерный энергосберегающий пакет", "price": 16_000},
    "tempered": {"label": "Калёное стекло", "price": 25_000},
}

FITTINGS_PRICE = 15_000       # фурнитура, фиксированная сумма на конструкцию
INSTALLATION_MARKUP = 0.20    # монтаж — 20% от суммы материалов

# Разумные границы ввода габаритов (защита от опечаток вроде "150" вместо "1.5")
MIN_DIMENSION_M = 0.3
MAX_DIMENSION_M = 20.0