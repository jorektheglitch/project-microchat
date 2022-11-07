from typing import Callable

from aiohttp import web

from microchat.storages import UoW
from microchat.services import ServiceSet

from .auth import router as auth_routes
from ..api_utils import Handler, Middleware


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
    auth_app = web.Application()
    auth_app.router.add_routes(auth_routes)
    api_app.add_subapp("/auth/", auth_app)
    return api_app
