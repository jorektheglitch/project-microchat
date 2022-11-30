from typing import Callable, Sequence

from aiohttp import web

from microchat.core.jwt_manager import JWTManager
from microchat.storages import UoW
from microchat.services import ServiceSet
from microchat.api_utils.types import Handler, Middleware

from .auth import router as auth_routes
from .chats import router as chats_routes
from .entities import router as entities_routes
from .media import router as media_routes


SUBROUTES: dict[str, Sequence[web.AbstractRouteDef]] = {
    "/auth/": auth_routes,
    "/chats/": chats_routes,
    "/entities/": entities_routes,
    "/media/": media_routes
}


def jwt_middleware(jwt_manager: JWTManager) -> Middleware:
    @web.middleware
    async def add_jwt_manager(
        request: web.Request, handler: Handler
    ) -> web.StreamResponse:
        request["jwt_manager"] = jwt_manager
        return await handler(request)
    return add_jwt_manager


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


def api_app(
    uow_factory: Callable[[], UoW],
    jwt_manager: JWTManager
) -> web.Application:
    api_app = web.Application(middlewares=[
        jwt_middleware(jwt_manager),
        services_middleware(uow_factory)
    ])
    for prefix, routes in SUBROUTES.items():
        subapp = web.Application()
        subapp.router.add_routes(routes)
        api_app.add_subapp(prefix, subapp)
    return api_app
