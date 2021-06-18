"""
Module for model's bases - useful functions, constants and Model base class.
"""

from functools import wraps

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.sql.expression import select, text


metadata = MetaData()
DeclarativeBase = declarative_base(metadata=metadata)

CASCADE = "CASCADE"
RESTRICT = "RESTRICT"
SET_DEFAULT = "SET DEFAULT"
SET_NULL = "SET NULL"


def new_session(metadata: MetaData = metadata, **kwargs) -> AsyncSession:
    """
    Creates a new session for DB.
    """
    return AsyncSession(metadata._bind, expire_on_commit=False, **kwargs)


def with_session(async_func):
    """
    Decorator that passes AsyncSession instance to 'session' keyword argument
    if function called without it.
    """
    @wraps(async_func)
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


async def create_median_function(conn):
    await conn.execute(text("""
        CREATE OR REPLACE FUNCTION _final_median(anyarray) RETURNS float8 AS $$
            WITH
                q AS (
                    SELECT val
                    FROM unnest($1) val
                    WHERE VAL IS NOT NULL
                    ORDER BY 1
                ),
                cnt AS (
                    SELECT COUNT(*) as c FROM q
                )
            SELECT
                AVG(val)::float8
            FROM (
                SELECT val FROM q
                LIMIT  2 - MOD((SELECT c FROM cnt), 2)
                OFFSET GREATEST(CEIL((SELECT c FROM cnt) / 2.0) - 1,0)  
            ) q2;
            $$ LANGUAGE sql IMMUTABLE;
    """))
    await conn.execute(text("""
        CREATE OR REPLACE AGGREGATE median(anyelement) (
            SFUNC=array_append,
            STYPE=anyarray,
            FINALFUNC=_final_median,
            INITCOND='{}'
        );
    """))


class Model(DeclarativeBase):
    """
    Base class for DB models.
    """

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
