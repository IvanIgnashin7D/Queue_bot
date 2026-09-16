import random
from datetime import datetime, timedelta

from bd.stmt import get_admins, get_queue_members


def calculate_random_open_time(target_dt: datetime) -> datetime:
    now = datetime.now()  # noqa: DTZ005

    if target_dt <= now:
        return now + timedelta(seconds=5)

    ideal_start = target_dt - timedelta(hours=2)

    start_window = max(now, ideal_start)

    total_seconds = int((target_dt - start_window).total_seconds())

    if total_seconds <= 10:
        return now + timedelta(seconds=5)

    random_seconds = random.randint(0, total_seconds)
    return start_window + timedelta(seconds=random_seconds)


async def create_new_text(queue_id: int) -> str:
    actual_members = await get_queue_members(queue_id=queue_id)
    members_text = "\n".join(
        [f"{m.position}. @{m.username} {m.first_name or ''}" for m in actual_members]
    )
    new_text = f"<b>Запись в очередь открыта!</b>\n\nСписок участников:\n{members_text}"
    return new_text


async def check_admin_status(tg_id: int) -> bool:
    admins = await get_admins()
    if not admins:
        return False
    for admin in admins:
        if admin.tg_id == tg_id:
            return True
    return False
