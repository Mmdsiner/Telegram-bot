from aiogram import Router, F
from aiogram.types import Message
from config import ADMIN_IDS

router = Router()

def is_admin(user_id):
    return user_id in ADMIN_IDS

@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    if is_admin(message.from_user.id):
        await message.answer("ادمین هستی ✅")
