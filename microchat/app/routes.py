from asyncio import Queue

from typing import AsyncIterable, Awaitable, Callable, TypeVar

from aiohttp import web
from aiohttp import typedefs

from microchat.api_utils.exceptions import APIError
from microchat.api_utils.handler import inject_services
from microchat.api_utils.request import APIRequest
from microchat.api_utils.response import APIResponse, DEFAULT_JSON_DUMPER
from microchat.api_utils.response import P, APIResponseBody, JSON

from microchat.core.events import Event
from microchat.core.jwt_manager import JWTManager
from microchat.services import ServiceError, ServiceSet
from microchat.storages import UoW

from .rendering import renderer


R = TypeVar("R", bound=APIRequest, contravariant=True)


class APIEndpoints:

    def __init__(
        self,
        uow_factory: Callable[[], UoW],
        jwt_manager: JWTManager,
        renderer: Callable[[APIResponse[APIResponseBody | JSON | AsyncIterable[bytes] | Queue[Event]] | APIError], Awaitable[web.StreamResponse]]
    ) -> None:
        self.uow_factory = uow_factory
        self.jwt_manager = jwt_manager
        self.renderer = renderer
        self._router = web.UrlDispatcher()

    def add_route(
        self,
        method: str,
        route: str,
        executor: Callable[[R, ServiceSet], Awaitable[APIResponse[P]]],
        extractor: Callable[[web.Request], Awaitable[R]]
    ) -> None:
        with_services = inject_services(executor, self.uow_factory, self.jwt_manager)
        handler = endpoint(with_services, extractor, self.renderer)
        self._router.add_route(method, route, handler)


def get_api_router(
    uow_factory: Callable[[], UoW],
    jwt_manager: JWTManager
) -> web.UrlDispatcher:
    render = renderer(DEFAULT_JSON_DUMPER)
    routes = APIEndpoints(uow_factory, jwt_manager, render)
    # TODO: add all routes 
    return routes._router


def endpoint(
    executor: Callable[[R], Awaitable[APIResponse[P]]],
    extractor: Callable[[web.Request], Awaitable[R]],
    renderer: Callable[[APIResponse[P] | APIError], Awaitable[web.StreamResponse]],
) -> typedefs.Handler:
    async def handler(request: web.Request) -> web.StreamResponse:
        api_response: APIResponse[P] | APIError
        try:
            api_request = await extractor(request)
            api_response = await executor(api_request)
        except APIError as err:
            api_response = err
        except ServiceError as service_exc:
            exc_info = APIError.from_service_exc(service_exc)
            api_response = exc_info
        reponse = await renderer(api_response)
        return reponse
    return handler
