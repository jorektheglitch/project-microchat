from typing import Awaitable, Callable, Sequence, TypeVar

from aiohttp import web
from microchat.api_utils.handler import api_handler
from microchat.api_utils.request import APIRequest
from microchat.api_utils.response import APIResponse

from microchat.core.jwt_manager import JWTManager
from microchat.storages import UoW
from microchat.services import ServiceSet
from microchat.api_utils.types import Handler, Middleware

from microchat.api.auth_ import add_session, list_sessions, terminate_session
from microchat.api.chats import router as chats_routes
from microchat.api.entities import router as entities_routes
from microchat.api.media import router as media_routes

from .api_adapters.auth import session_add_params, session_close_params, sessions_request_params


R = TypeVar("R", bound=APIRequest, contravariant=True)

APIRoute = tuple[str, str, Callable[[R, ServiceSet], Awaitable[APIResponse]], Callable[[web.Request], Awaitable[R]]]
auth_routes = web.UrlDispatcher()
auth_routes.add_route("GET", "/sessions", api_handler(list_sessions))
auth_routes_: list[APIRoute[APIRequest]] = [
    ("GET", "/sessions", list_sessions, sessions_request_params, authenticate),
    ("POST", "/sessions", add_session, session_add_params),
    (r"/sessions/{session_id:\w+}", terminate_session, session_close_params)
]


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
