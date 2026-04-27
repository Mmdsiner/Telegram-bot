import sys
import os
import asyncio

# حل مشکل پیدا نکردن ماژول bot
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from config import BOT_TOKEN

# ایمپورت هندلرها
from handlers import user, admin, payment

async def main():
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # ثبت هندلرها
    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(payment.router)

    print("Bot is running...")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
