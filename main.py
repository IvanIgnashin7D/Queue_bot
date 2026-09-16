import asyncio
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from bd.base import init_db
from bot.handlers import router, scheduler
from bot.handlers_private import router_private

load_dotenv()
TOKEN = getenv("BOT_TOKEN", "")


async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        await init_db()

        if TOKEN is None:
            raise RuntimeError("BOT_TOKEN is not set")

        dp = Dispatcher()

        scheduler.start()

        await bot.delete_webhook(drop_pending_updates=True)
        dp.include_routers(router, router_private)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped!")
