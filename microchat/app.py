from logging import Logger

from typing import Awaitable, Callable, Iterable

from aiohttp import log
from aiohttp import web
from aiohttp.typedefs import Handler

from .api import api_app
from .core.jwt_manager import JWTManager
from .storages import UoW


_Middleware = Callable[[web.Request, Handler], Awaitable[web.StreamResponse]]


async def app(
    uow_factory: Callable[[], UoW],
    jwt_manager: JWTManager,
    logger: Logger = log.web_logger,
    middlewares: Iterable[_Middleware] = (),
    client_max_size: int = 1024**2,
) -> web.Application:
    router = web.UrlDispatcher()
    app = web.Application(
        logger=logger, router=router, middlewares=middlewares,
        client_max_size=client_max_size
    )
    app.add_subapp("/api/", api_app(uow_factory, jwt_manager))
    return app
