from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from keyboards import main_menu, plan_menu
from states import BuyState
from database import fetch, execute
from config import SUPPORT_ID

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    await execute(
        "INSERT INTO users(user_id) VALUES($1) ON CONFLICT DO NOTHING",
        message.from_user.id
    )
    await message.answer("خوش اومدی", reply_markup=main_menu())


@router.callback_query(F.data == "support")
async def support(call: CallbackQuery):
    await call.message.answer(SUPPORT_ID)


@router.callback_query(F.data == "buy")
async def buy(call: CallbackQuery, state: FSMContext):
    await state.set_state(BuyState.plan)
    await call.message.answer("نوع سرویس:", reply_markup=plan_menu())


@router.callback_query(F.data.startswith("plan_"))
async def choose_plan(call: CallbackQuery, state: FSMContext):
    plan = call.data.split("_")[1]
    await state.update_data(plan=plan)
    await state.set_state(BuyState.amount)
    await call.message.answer("چند گیگ؟")


@router.message(BuyState.amount)
async def amount(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("عدد بفرست")

    amount = int(message.text)
    data = await state.get_data()

    price_key = "normal_price" if data["plan"] == "normal" else "vip_price"

    price = await fetch("SELECT value FROM settings WHERE key=$1", price_key)
    price = int(price[0]["value"])

    discount = await fetch("SELECT value FROM settings WHERE key='discount'")
    discount = int(discount[0]["value"])

    total = amount * price
    total -= total * discount // 100

    await state.update_data(total=total)

    await message.answer(f"مبلغ: {total} تومان\nرسید رو بفرست")
