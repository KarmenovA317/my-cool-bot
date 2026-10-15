"""
sheets_db.py
Запись лидов в Google Таблицу через gspread (сервисный аккаунт Google).

gspread — синхронная библиотека, поэтому все обращения к API выполняются
в отдельном потоке через asyncio.to_thread, чтобы не блокировать event loop
бота во время сетевого запроса к Google.
"""
import logging
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_ID, GOOGLE_SHEET_WORKSHEET

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADER = [
    "Дата и время",
    "Имя",
    "Телефон",
    "Тип профиля",
    "Стекло",
    "Габариты (ШхВ)",
    "Предварительная стоимость",
    "Статус",
]

_worksheet = None  # кэш открытого листа, чтобы не переавторизовываться на каждый лид


def _get_worksheet():
    global _worksheet
    if _worksheet is not None:
        return _worksheet

    creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(GOOGLE_SHEET_ID)

    try:
        ws = spreadsheet.worksheet(GOOGLE_SHEET_WORKSHEET)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=GOOGLE_SHEET_WORKSHEET, rows=1000, cols=len(HEADER))

    if ws.row_values(1) != HEADER:
        ws.insert_row(HEADER, 1)

    _worksheet = ws
    return _worksheet


def _write_lead_sync(
    name: str,
    phone: str,
    profile_type: str,
    glass_type: str,
    dimensions: str,
    total_cost: str,
) -> None:
    ws = _get_worksheet()
    row = [
        datetime.now().strftime("%d.%m.%Y %H:%M"),
        name,
        phone,
        profile_type,
        glass_type,
        dimensions,
        total_cost,
        "Новый",
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")


async def add_lead(
    name: str,
    phone: str,
    profile_type: str,
    glass_type: str,
    dimensions: str,
    total_cost: str,
) -> None:
    """Асинхронно добавляет строку с лидом в Google Таблицу."""
    import asyncio

    try:
        await asyncio.to_thread(
            _write_lead_sync, name, phone, profile_type, glass_type, dimensions, total_cost
        )
    except Exception:
        logger.exception("Не удалось записать лид в Google Sheets")
        raise