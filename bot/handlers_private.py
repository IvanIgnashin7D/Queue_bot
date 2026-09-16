from os import getenv

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dotenv import load_dotenv

from bd.states import StatusAuth
from bd.stmt import add_admin, get_admin

router_private = Router()
router_private.message.filter(F.chat.type == ChatType.PRIVATE)

load_dotenv()
ADMIN_PASS = getenv("ADMIN_PASS", "")


@router_private.message(F.text.strip().lower() == "стать админом")
async def add_admin_handler(message: Message, state: FSMContext):
    tg_id = message.from_user.id

    existing_admin = await get_admin(tg_id=tg_id)
    if existing_admin:
        await message.answer("Ты уже админ")
        return

    await message.answer("Введите пароль \nДля отмены введите /cancel")
    await state.set_state(StatusAuth.waiting_for_password)


@router_private.message(Command("cancel"), StatusAuth.waiting_for_password)
async def cancel_auth(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отмена")


@router_private.message(StatusAuth.waiting_for_password, F.text)
async def check_password(message: Message, state: FSMContext):
    entered_password = message.text.strip()

    if entered_password == ADMIN_PASS:
        await add_admin(message.from_user.id)

        await message.answer("Вам присвоен статус администратора.")
        await state.clear()
    else:
        await message.answer(
            "Неверный пароль. Попробуйте еще раз или напишите /cancel."
        )
