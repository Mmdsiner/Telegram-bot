from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("🤖 ربات با موفقیت فعال شد!")    await state.set_state(BuyState.amount)
    await message.answer("چند گیگ؟")


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
