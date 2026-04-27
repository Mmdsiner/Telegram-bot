from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database import execute, fetch
from keyboards import payment_actions
from config import ADMIN_IDS

router = Router()

# دریافت رسید
@router.message(F.photo)
async def receipt(message: Message):
    user_id = message.from_user.id

    # ذخیره پرداخت
    await execute(
        "INSERT INTO payments(user_id,amount,status) VALUES($1,$2,'pending')",
        user_id, 0
    )

    payment = await fetch("SELECT id FROM payments ORDER BY id DESC LIMIT 1")
    payment_id = payment[0]["id"]

    # ارسال برای ادمین
    for admin in ADMIN_IDS:
        await message.bot.send_photo(
            admin,
            message.photo[-1].file_id,
            caption=f"رسید جدید\nUser: {user_id}",
            reply_markup=payment_actions(payment_id)
        )

    await message.answer("ارسال شد، منتظر تایید")


# تایید
@router.callback_query(F.data.startswith("approve_"))
async def approve(call: CallbackQuery):
    payment_id = int(call.data.split("_")[1])

    payment = await fetch("SELECT user_id FROM payments WHERE id=$1", payment_id)
    user_id = payment[0]["user_id"]

    await execute("UPDATE payments SET status='approved' WHERE id=$1", payment_id)

    # ارسال سرویس (نمونه)
    await call.bot.send_message(user_id, "✅ پرداخت تایید شد\nسرویس شما:\nvpn://example")

    await call.message.edit_caption("✅ تایید شد")


# رد
@router.callback_query(F.data.startswith("reject_"))
async def reject(call: CallbackQuery):
    payment_id = int(call.data.split("_")[1])

    payment = await fetch("SELECT user_id FROM payments WHERE id=$1", payment_id)
    user_id = payment[0]["user_id"]

    await execute("UPDATE payments SET status='rejected' WHERE id=$1", payment_id)

    await call.bot.send_message(user_id, "❌ پرداخت رد شد")

    await call.message.edit_caption("❌ رد شد")
