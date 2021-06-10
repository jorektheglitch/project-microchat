from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.sql.expression import select


metadata = MetaData()
DeclarativeBase = declarative_base(metadata=metadata)

CASCADE = "CASCADE"
RESTRICT = "RESTRICT"
SET_DEFAULT = "SET DEFAULT"
SET_NULL = "SET NULL"


def new_session(metadata: MetaData = metadata, **kwargs) -> AsyncSession:
    return AsyncSession(metadata._bind, expire_on_commit=False, **kwargs)


def with_session(async_func):
    async def wrapped(*args, **kwargs):
        if "session" in kwargs:
            result = await async_func(*args, **kwargs)
        else:
            result = await with_temp_session(async_func, *args, **kwargs)
        return result
    return wrapped


async def with_temp_session(async_func, *args, **kwargs):
    async with new_session() as session:
        return await async_func(*args, session=session, **kwargs)


class Model(DeclarativeBase):

    __abstract__ = True

    @classmethod
    def session(cls):
        return AsyncSession(cls.metadata._bind, expire_on_commit=False)

    @classmethod
    def filter(cls, *args, **kwargs):
        return select(cls).filter(*args, **kwargs)

    @classmethod
    @with_session
    async def get(cls, *PKs, session, **kwargs):
        obj = await session.get(cls, *PKs, **kwargs)
        return obj

    @with_session
    async def store(self, *, session):
        session.add(self)
        await session.commit()
