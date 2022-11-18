from typing import Callable, Sequence

from aiohttp import web

from microchat.storages import UoW
from microchat.services import ServiceSet

from .auth import router as auth_routes
from .chats import router as chats_routes
from .entities import router as entities_routes
from .media import router as media_routes
from ..api_utils import Handler, Middleware


SUBROUTES: dict[str, Sequence[web.AbstractRouteDef]] = {
    "/auth/": auth_routes,
    "/chats/": chats_routes,
    "/entities/": entities_routes,
    "/media/": media_routes
}


def services_middleware(uow_factory: Callable[[], UoW]) -> Middleware:
    @web.middleware
    async def add_services(
        request: web.Request, handler: Handler
    ) -> web.StreamResponse:
        async with uow_factory() as uow:
            services = ServiceSet(uow)
            request["services"] = services
            return await handler(request)
    return add_services


def api_app(uow_factory: Callable[[], UoW]) -> web.Application:
    api_app = web.Application(middlewares=[
        services_middleware(uow_factory)
    ])
    for prefix, routes in SUBROUTES.items():
        subapp = web.Application()
        subapp.router.add_routes(routes)
        api_app.add_subapp(prefix, subapp)
    return api_app
