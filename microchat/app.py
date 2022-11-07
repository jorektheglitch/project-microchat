from logging import Logger

from typing import Any, Awaitable, Callable, Iterable

from aiohttp import log
from aiohttp import web
from aiohttp.typedefs import Handler

from .api import api_app
from .storages import UoW


_Middleware = Callable[[web.Request, Handler], Awaitable[web.StreamResponse]]


async def app(  # type: ignore
    uow_factory: Callable[[], UoW],
    logger: Logger = log.web_logger,
    middlewares: Iterable[_Middleware] = (),
    handler_args: dict[str, Any] = None,
    client_max_size: int = 1024**2,
) -> web.Application:
    web.json_response()
    router = web.UrlDispatcher()
    app = web.Application(
        logger=logger, router=router, middlewares=middlewares,
        handler_args=handler_args, client_max_size=client_max_size
    )
    app.add_subapp("/api/", api_app(uow_factory))
    return app
