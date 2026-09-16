from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def create_kb_queue(queue_id: int) -> InlineKeyboardMarkup:
    kb_queue = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Занять", callback_data=f"enter_queue_{queue_id}"
                ),
                InlineKeyboardButton(
                    text="Покинуть", callback_data=f"leave_queue_{queue_id}"
                ),
                InlineKeyboardButton(
                    text="Удалить",
                    callback_data=f"delete_queue_{queue_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Продвинуть очередь", callback_data=f"move_queue_{queue_id}"
                )
            ],
        ]
    )
    return kb_queue
