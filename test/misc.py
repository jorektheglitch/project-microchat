import asyncio

from app.models import User, Message
from app.models import new_session, store


def async_to_sync(async_func):
    def wrapped(*args, **kwargs):
        loop = asyncio.get_event_loop()
        coro = async_func(*args, **kwargs)
        return loop.run_until_complete(coro)
    return wrapped


def with_session(async_func):
    async def wrapped(*args, **kwargs):
        async with new_session() as session:
            return await async_func(*args, session=session, **kwargs)
    return wrapped


async def fill_database():
    await create_users()
    await create_private_messages()


async def create_users():
    users = [User(username=str(i)) for i in range(5)]
    await store(*users)


async def create_private_messages():
    pairs = (1, 2), (2, 1), (3, 2), (2, 3)
    for i in range(20):
        m = Message(text="test{}".format(i))
        sender, receiver = pairs[i % 4]
        await m.bind(sender=sender, receiver=receiver)

asnc_test = async_to_sync
