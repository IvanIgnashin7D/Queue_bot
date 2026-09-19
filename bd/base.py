from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

engine = create_async_engine("sqlite+aiosqlite:///bot.db", echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


class Base(DeclarativeBase):
    pass


class Model(Base):
    __abstract__ = True
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class Queue(Model):
    __tablename__ = "queues"
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    topic_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    creator_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    open_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    name: Mapped[str] = mapped_column(String(30), nullable=False)


class User(Model):
    __tablename__ = "users"
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str | None] = mapped_column(String(25), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(25), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    queue_id: Mapped[int] = mapped_column(ForeignKey("queues.id"), nullable=False)


class Admin(Model):
    __tablename__ = "admins"
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
