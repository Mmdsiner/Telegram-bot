from aiogram.fsm.state import StatesGroup, State

class BuyState(StatesGroup):
    plan = State()
    amount = State()

class AdminState(StatesGroup):
    set_discount = State()
