import asyncio
from datetime import datetime
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from bd.base import init_db
from bd.stmt import get_pending_queues
from bot.handlers import publish_queue_job, router, scheduler
from bot.handlers_private import router_private


async def restore_jobs(bot: Bot):
    pending_queues = await get_pending_queues()
    now = datetime.now()  # noqa: DTZ005

    for queue in pending_queues:
        if queue.open_time <= now:
            await publish_queue_job(bot=bot, queue_id=queue.id)
        else:
            scheduler.add_job(
                publish_queue_job,
                trigger="date",
                run_date=queue.open_time,
                kwargs={"bot": bot, "queue_id": queue.id},
            )

    if pending_queues:
        print(f"Восстановлено задач публикаций: {len(pending_queues)}")


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
        await restore_jobs(bot)

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
