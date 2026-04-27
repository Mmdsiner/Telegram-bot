async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    await connect()
    await init_db()

    await bot.delete_webhook(drop_pending_updates=True)

    dp.include_router(user.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)

    await dp.start_polling(bot)
