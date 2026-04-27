import asyncio
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import connect, init_db

from handlers import user, admin, payment

async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    await connect()
    await init_db()

    dp.include_router(user.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
