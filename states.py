"""
states.py
Состояния конечного автомата (FSM) для сценария калькулятора и заявки.
"""
from aiogram.fsm.state import State, StatesGroup


class OrderForm(StatesGroup):
    choosing_profile = State()   # выбор типа профиля
    choosing_glass = State()     # выбор типа остекления
    entering_width = State()     # ввод ширины
    entering_height = State()    # ввод высоты
    entering_name = State()      # ввод имени для заявки
    entering_phone = State()     # ожидание контакта (номера телефона)