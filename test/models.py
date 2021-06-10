import unittest
import asyncio
import logging
import warnings

# from sqlalchemy import exc

from app.models import User, Message
from app.models import init, drop, metadata
from app.api.sse.handlers import sse_api

from .misc import async_test, with_session, fill_database


dbms = "postgresql"
driver = "asyncpg"
user = "microchat_admin"
password = "microchat"
domain = "127.0.0.1"
port = 6543
database = "test"

db = "{}+{}://{}:{}@{}:{}/{}".format(
        dbms,
        driver,
        user,
        password,
        domain,
        port,
        database
    )

logging.basicConfig()


def enable_full_log():
    logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.DEBUG)
# enable_full_log()


class TestSetUpFail(Exception): ...  # noqa


class TestDBModels(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.debug("Setting up test environment...")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(init(db))
        try:
            loop.run_until_complete(fill_database())
        except Exception as e:
            cls.tearDownClass()
            raise TestSetUpFail from e

    @classmethod
    def tearDownClass(cls):
        logging.debug("Cleaning test environment...")
        async def cleanup():  # noqa
            await drop(metadata)
            await sse_api.stop()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(cleanup())

    @async_test
    @with_session
    async def test_create_users(self, session):
        pass

    @async_test
    @with_session
    async def test_getting_object(self, session):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            for Model in User, Message:
                obj = await session.get(Model, 1)
                self.assertTrue(obj)

    @async_test
    @with_session
    async def test_getting_pm_history(self, session):
        user: User = await session.get(User, 1)
        messages = await user.get_personal_history(
            other=2,
            offset=0,
            limit=100
        )
        self.assertTrue(messages, "No messages fetched")
        self.assertEqual(len(messages), 10, "Collected more/less than 10 messages")  # noqa
        users_ids = 1, 2
        for message, mid, receiver, sender in messages:  # noqa
            self.assertIn(sender, users_ids, "Unexpected sender value")
            self.assertIn(receiver, users_ids, "Unexpected receiver value")

    @async_test
    @with_session
    async def test_getting_pm_overview(self, session):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            user: User = await session.get(User, 1)
            overview = await user.pm_overview()
        self.assertTrue(overview)

    @async_test
    @with_session
    async def test_storing_pm(self, session):
        for i in range(10):
            params = {
                "sender": (i % 3)+1,
                "receiver": (i % 3)+2
            }
            m = Message(text="test{}".format(i))
            await m.bind(**params)
