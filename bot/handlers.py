from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bd.stmt import (
    add_user,
    create_new_queue,
    delete_queue,
    delete_user,
    get_user,
    move_queue,
    update_queue_message_id,
)
from bot.keyboards import create_kb_queue
from bot.utils import calculate_random_open_time, check_admin_status, create_new_text

router = Router()
scheduler = AsyncIOScheduler()

# user {message.from_user.id} said: {message.text}
# chat: {message.chat.id}, topic: {message.message_thread_id}, message_id: {message.message_id}
# is topic message: {message.is_topic_message}


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer("Стартуем!")


@router.message(Command("new_queue"))
async def new_queue_handler(message: Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.reply("Формат: <code>/new_queue ГГГГ-ММ-ДД ЧЧ:ММ</code>")
        return

    try:
        target_dt = datetime.strptime(f"{args[1]} {args[2]}", "%Y-%m-%d %H:%M")  # noqa: DTZ007
    except ValueError:
        await message.reply("Неверный формат даты/времени!")
        return

    queue = await create_new_queue(
        chat_id=message.chat.id,
        creator_id=message.from_user.id,
        topic_id=message.message_thread_id,
    )

    if not queue:
        await message.reply("Очередь уже существует")
        return

    open_time = calculate_random_open_time(target_dt)

    scheduler.add_job(
        publish_queue_job,
        trigger="date",
        run_date=open_time,
        kwargs={
            "message": message,
            "queue_id": queue.id,
        },
    )

    await message.reply(
        f"Очередь создана! Запись откроется случайным образом до {target_dt.strftime('%H:%M')}."
    )


async def publish_queue_job(message: Message, queue_id: int):
    text = (
        "<b>Запись в очередь открыта!</b>\n\nСписок участников:\n<i>Пока никого нет</i>"
    )

    msg = await message.answer(
        text=text,
        reply_markup=create_kb_queue(queue_id),
        parse_mode="HTML",
    )
    await update_queue_message_id(id=queue_id, message_id=msg.message_id)


@router.callback_query(F.data.startswith("enter_queue_"))
async def enter_queue_handler(callback_query):
    queue_id = int(callback_query.data.split("_")[2])
    tg_id = callback_query.from_user.id
    username = callback_query.from_user.username or callback_query.from_user.full_name
    first_name = callback_query.from_user.first_name

    existing_user = await get_user(tg_id=tg_id, queue_id=queue_id)
    if existing_user:
        await callback_query.answer("Ты уже в очереди!", show_alert=True)
        return

    await add_user(
        tg_id=tg_id, queue_id=queue_id, username=username, first_name=first_name
    )

    await callback_query.answer("Теперь ты записан")

    new_text = await create_new_text(queue_id=queue_id)
    try:
        await callback_query.message.edit_text(
            text=new_text,
            reply_markup=create_kb_queue(queue_id),
            parse_mode="HTML",
        )
    except Exception:  # noqa: BLE001, S110
        pass


@router.callback_query(F.data.startswith("leave_queue_"))
async def leave_queue_handler(callback_query):
    queue_id = int(callback_query.data.split("_")[2])
    tg_id = callback_query.from_user.id

    existing_member = await get_user(tg_id=tg_id, queue_id=queue_id)

    if not existing_member:
        await callback_query.answer("Ты и так не в очереди", show_alert=True)

    await delete_user(tg_id=tg_id, queue_id=queue_id)

    new_text = await create_new_text(queue_id=queue_id)

    try:
        await callback_query.message.edit_text(
            text=new_text,
            reply_markup=create_kb_queue(queue_id),
            parse_mode="HTML",
        )
        await callback_query.answer("Ты покинул очередь")
    except Exception:  # noqa: BLE001, S110
        pass


@router.callback_query(F.data.startswith("delete_queue_"))
async def delete_queue_handler(callback_query):
    if not await check_admin_status(callback_query.from_user.id):
        await callback_query.answer(
            "Удалять очередь могут только админы", show_alert=True
        )
        return

    queue_id = int(callback_query.data.split("_")[2])
    await delete_queue(id=queue_id)
    await callback_query.answer("Очередь удалена")
    await callback_query.message.delete()


@router.callback_query(F.data.startswith("move_queue_"))
async def move_queue_handler(callback_query):
    queue_id = int(callback_query.data.split("_")[2])
    await move_queue(id=queue_id)

    new_text = await create_new_text(queue_id=queue_id)
    try:
        await callback_query.message.edit_text(
            text=new_text,
            reply_markup=create_kb_queue(queue_id),
            parse_mode="HTML",
        )
        await callback_query.answer("Очередь продвинута", show_alert=True)
    except Exception:  # noqa: BLE001, S110
        pass
