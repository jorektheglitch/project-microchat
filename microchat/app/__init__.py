from contextlib import asynccontextmanager
from logging import Logger

from typing import AsyncGenerator, Awaitable, Callable, Iterable


from aiohttp import log
from aiohttp import web
from aiohttp.typedefs import Handler

from microchat.api_utils.response import DEFAULT_JSON_DUMPER
from microchat.app.rendering import renderer
from microchat.core.jwt_manager import JWTManager
from microchat.services import ServiceSet
from microchat.storages import UoW

from .api_adapters import routes


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


async def render_api_error(request: web.Request, exc: Exception) -> web.Response:
    return web.json_response(status=502)


def api_app(
    uow_factory: Callable[[], UoW],
    jwt_manager: JWTManager
) -> web.Application:
    @asynccontextmanager
    async def ctx_factory() -> AsyncGenerator[tuple[ServiceSet], None]:
        async with uow_factory() as uow:
            services = ServiceSet(uow, jwt_manager)
            yield (services, )

    render = renderer(DEFAULT_JSON_DUMPER)
    router = web.UrlDispatcher()
    for route in routes:
        handler = route.handler.configure(ctx_factory=ctx_factory, presenter=render, error_presenter=render_api_error)
        router.add_route(method=route.method, path=route.path, handler=handler)
    api_app = web.Application(router=router)
    return api_app
