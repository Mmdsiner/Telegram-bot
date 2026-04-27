import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import connect, init_db

from handlers import user, payment, admin


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # اتصال دیتابیس
    await connect()
    await init_db()

    # حل مشکل webhook و conflict
    await bot.delete_webhook(drop_pending_updates=True)

    # ثبت هندلرها
    dp.include_router(user.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)

    print("BOT STARTED ✅")

    # اجرای ربات
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
