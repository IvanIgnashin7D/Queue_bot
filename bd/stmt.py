from datetime import datetime

from sqlalchemy import delete, select, update

from bd.base import Admin, Base, Queue, User, async_session, engine


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def create_new_queue(
    chat_id: int,
    creator_id: int,
    open_time: datetime,
    name: str,
    topic_id: int | None = None,
) -> Queue:
    async with async_session() as session:
        existing_queue = await get_queue_by_chat_and_name(
            name=name, chat_id=chat_id, topic_id=topic_id
        )
        if existing_queue:
            return None
        new_queue = Queue(
            chat_id=chat_id,
            topic_id=topic_id,
            creator_id=creator_id,
            open_time=open_time,
            name=name,
        )
        session.add(new_queue)
        await session.commit()
        await session.refresh(new_queue)
        return new_queue


async def add_user(
    tg_id: int,
    queue_id: int,
    username: str | None = None,
    first_name: str | None = None,
) -> User:
    async with async_session() as session:
        stmt = select(User).filter_by(tg_id=tg_id, queue_id=queue_id)
        users = await session.scalars(stmt)
        if not users.all():
            queue_users = await get_queue_members(queue_id)
            user = User(
                tg_id=tg_id,
                queue_id=queue_id,
                username=username,
                position=len(queue_users) + 1,
                first_name=first_name,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
    return None


async def get_queue_members(queue_id: int) -> list[User]:
    async with async_session() as session:
        stmt = select(User).filter_by(queue_id=queue_id).order_by(User.position)
        queue_members = await session.scalars(stmt)
        return queue_members.all()


async def get_queues_by_chat(chat_id: int, topic_id: int | None = None) -> list[Queue]:
    async with async_session() as session:
        stmt = select(Queue).filter_by(chat_id=chat_id, topic_id=topic_id)
        queues = await session.scalars(stmt)
        return list(queues.all())


async def get_queue_by_id(id: int) -> Queue:
    async with async_session() as session:
        stmt = select(Queue).filter_by(id=id)
        queue = await session.scalars(stmt)
        if queue:
            return queue.first()
        return None


async def get_queue_by_chat_and_name(
    name: str, chat_id: int, topic_id: int | None = None
):
    async with async_session() as session:
        stmt = select(Queue).filter_by(name=name, chat_id=chat_id, topic_id=topic_id)
        queue = await session.scalars(stmt)
        if queue:
            return queue.first()
        return None


async def get_users():
    async with async_session() as session:
        stmt = select(User)
        users = await session.scalars(stmt)
        return users.all()


async def delete_queue(id: int):
    async with async_session() as session:
        stmt = select(Queue).filter_by(id=id)
        queue = await session.scalars(stmt)
        queue_to_delete = queue.first()

        if queue_to_delete:
            stmt = delete(User).filter_by(queue_id=id)
            await session.execute(stmt)
            await session.delete(queue_to_delete)
            await session.commit()


async def delete_user(tg_id: int, queue_id: int) -> User:
    async with async_session() as session:
        queue_members = await get_queue_members(queue_id)
        if len(queue_members) >= 1:
            user_to_delete = None

            for user in queue_members:
                if user.tg_id == tg_id:
                    user_to_delete = user

            if not user_to_delete:
                return None

            if len(queue_members) == 1:
                await session.delete(user_to_delete)
                await session.commit()
                return user_to_delete

            stmt = (
                update(User)
                .where(
                    User.queue_id == queue_id, User.position > user_to_delete.position
                )
                .values(position=User.position - 1)
            )
            await session.execute(stmt)
            await session.delete(user_to_delete)
            await session.commit()
            return user_to_delete


async def move_queue(id: int):
    async with async_session() as session:
        queue_members = await get_queue_members(id)

        if len(queue_members) >= 1:
            await delete_user(queue_members[0].tg_id, id)
            await session.commit()


async def update_queue_message_id_and_open(id: int, message_id: int):
    async with async_session() as session:
        stmt = update(Queue).filter_by(id=id).values(message_id=message_id, opened=True)
        await session.execute(stmt)
        await session.commit()


async def get_user(tg_id: int, queue_id: int) -> User:
    async with async_session() as session:
        stmt = select(User).filter_by(tg_id=tg_id, queue_id=queue_id)
        user = await session.scalars(stmt)
        return user.first()


async def get_admins() -> list[Admin]:
    async with async_session() as session:
        stmt = select(Admin)
        admins = await session.scalars(stmt)
    return admins.all()


async def add_admin(tg_id: int) -> Admin:
    async with async_session() as session:
        admin = Admin(tg_id=tg_id)
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
    return admin


async def get_admin(tg_id: int) -> Admin:
    async with async_session() as session:
        stmt = select(Admin).filter_by(tg_id=tg_id)
        admins = await session.scalars(stmt)
    return admins.first()


async def delete_admin(tg_id: int):
    async with async_session() as session:
        stmt = delete(Admin).filter_by(tg_id=tg_id)
        await session.execute(stmt)
        await session.commit()
