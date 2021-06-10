from pathlib import Path
from ipaddress import ip_network

from aiohttp import web

from app.middlewares import filter_ip, disable_caching, server_timing
from utils import redirect

from .api import api
from .api.sse.handlers import sse_api
from .models import init

from config import DB_OPTIONS


DB = "postgresql+asyncpg://microchat_admin:microchat@127.0.0.1:6543/future"


async def startup(app):
    await init(DB, **DB_OPTIONS)


async def shutdown(app):
    await sse_api.stop()


async def get_app() -> web.Application:
    app = web.Application(
        middlewares=[
            # filter_ip(ip_network("200::/7")),
            disable_caching,
            server_timing
        ]
    )

    app.add_subapp("/api/", api)

    app.router.add_get('/', redirect('/index'))
    app.router.add_get('/index', redirect('/index.html'))
    app.router.add_get('/register', redirect('/register.html'))

    app.router.add_static('/', Path('./www'))

    app.on_startup.append(startup)
    app.on_shutdown.append(shutdown)
    return app
