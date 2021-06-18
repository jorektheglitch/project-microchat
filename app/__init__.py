from aiohttp import web

from app.middlewares import disable_caching, server_timing
from utils import redirect

from .api import api
from .api.sse.handlers import sse_api
from .models import init

from config import DB, DB_OPTIONS


# TODO: remove DB address overwrite
DB = "postgresql+asyncpg://microchat_admin:microchat@127.0.0.1:6543/future"  # noqa


async def startup(app):
    await init(DB, **DB_OPTIONS)


async def shutdown(app):
    await sse_api.stop()


async def get_app() -> web.Application:
    app = web.Application(
        middlewares=[
            disable_caching,
            server_timing
        ]
    )

    app.add_subapp("/api/", api)

    app.router.add_get('/', redirect('/index.html'))
    app.router.add_get('/index', redirect('/index.html'))

    app.on_startup.append(startup)
    app.on_shutdown.append(shutdown)
    return app
