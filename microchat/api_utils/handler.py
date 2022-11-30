from __future__ import annotations
from asyncio import Queue
import asyncio

import enum
import json
import functools

from typing import AsyncIterable, ParamSpec, TypeVar
from typing import Awaitable, Callable, Literal, TypeGuard
from typing import overload
from typing import TYPE_CHECKING

from aiohttp_sse import sse_response
if TYPE_CHECKING:
    from .types import AuthenticatedHandler, APIHandler
    from .types import APIResponse, APIResponseEncoder
    from .types import Handler

from aiohttp import web
from aiohttp import typedefs

from microchat.services import ServiceError, ServiceSet
from microchat.core.entities import User

from .exceptions import APIError
from .response import DEFAULT_JSON_DUMPER


P = ParamSpec("P")
T = TypeVar("T")


class AccessLevel(enum.Enum):
    ANY = enum.auto()
    USER = enum.auto()
    MODERATOR = enum.auto()
    ADMIN = enum.auto()


@overload
def api_handler() -> Callable[[AuthenticatedHandler], Callable[[web.Request], Awaitable[web.StreamResponse]]]: ...
@overload  # noqa
def api_handler(
    *,
    access_level: Literal[AccessLevel.ANY],
    encoder: type[json.JSONEncoder] = APIResponseEncoder
) -> Callable[[APIHandler], Callable[[web.Request], Awaitable[web.StreamResponse]]]: ...
@overload  # noqa
def api_handler(
    *,
    access_level: Literal[AccessLevel.USER, AccessLevel.MODERATOR, AccessLevel.ADMIN],
    encoder: type[json.JSONEncoder] = APIResponseEncoder
) -> Callable[[AuthenticatedHandler], Callable[[web.Request], Awaitable[web.StreamResponse]]]: ...
@overload  # noqa
def api_handler(
    handler: AuthenticatedHandler
) -> Callable[[web.Request], Awaitable[web.StreamResponse]]: ...
@overload  # noqa
def api_handler(
    handler: APIHandler,
    *,
    access_level: Literal[AccessLevel.ANY],
    encoder: type[json.JSONEncoder] = APIResponseEncoder
) -> Callable[[web.Request], Awaitable[web.StreamResponse]]: ...
@overload  # noqa
def api_handler(
    handler: AuthenticatedHandler,
    *,
    access_level: Literal[AccessLevel.USER, AccessLevel.MODERATOR, AccessLevel.ADMIN] = AccessLevel.USER,
    encoder: type[json.JSONEncoder] = APIResponseEncoder
) -> Callable[[web.Request], Awaitable[web.StreamResponse]]: ...

def api_handler(  # noqa
    handler: APIHandler | AuthenticatedHandler | None = None,
    *,
    access_level: AccessLevel = AccessLevel.USER,
    encoder: type[json.JSONEncoder] = APIResponseEncoder
) -> Handler | Callable[[APIHandler], Handler] | Callable[[AuthenticatedHandler], Handler]:
    if handler is None:

        def wrap(handler: APIHandler) -> Handler:
            return wrap_api_handler(handler, access_level, encoder=encoder)

        def wrap_authenticated(handler: AuthenticatedHandler) -> Handler:
            return wrap_api_handler(handler, access_level, encoder=encoder)

        if access_level is AccessLevel.ANY:
            return wrap
        elif access_level in [AccessLevel.USER, AccessLevel.MODERATOR, AccessLevel.ADMIN]:
            return wrap_authenticated
        return wrap_authenticated

    return wrap_api_handler(handler, access_level, encoder=encoder)


@overload
def wrap_api_handler(
    handler: APIHandler,
    access_level: Literal[AccessLevel.ANY],
    *,
    encoder: type[json.JSONEncoder]
) -> Callable[[web.Request], Awaitable[web.StreamResponse]]: ...
@overload  # noqa
def wrap_api_handler(
    handler: AuthenticatedHandler,
    access_level: Literal[AccessLevel.USER, AccessLevel.MODERATOR, AccessLevel.ADMIN],
    *,
    encoder: type[json.JSONEncoder]
) -> Callable[[web.Request], Awaitable[web.StreamResponse]]: ...
@overload  # noqa
def wrap_api_handler(
    handler: APIHandler | AuthenticatedHandler,
    access_level: AccessLevel,
    *,
    encoder: type[json.JSONEncoder]
) -> Callable[[web.Request], Awaitable[web.StreamResponse]]: ...


def wrap_api_handler(
    handler: APIHandler | AuthenticatedHandler,
    access_level: AccessLevel,
    *,
    encoder: type[json.JSONEncoder]
) -> Callable[[web.Request], Awaitable[web.StreamResponse]]:
    dumps = functools.partial(json.dumps, cls=encoder)
    if authenticated_handler(handler, access_level):
        handler = authenticated(handler)
    if not default_handler(handler, AccessLevel.ANY):
        # never happens, just for type checker
        raise RuntimeError
    api_handler = with_services(handler)
    wrapped_handler = wrap_api_response(api_handler, dumps)
    return wrapped_handler


def with_services(
    handler: Callable[[web.Request, ServiceSet], Awaitable[T]]
) -> Callable[[web.Request], Awaitable[T]]:
    @functools.wraps(handler)
    async def wrapped(request: web.Request) -> T:
        services: ServiceSet = request["services"]
        return await handler(request, services)
    return wrapped


def authenticated(
    handler: Callable[[web.Request, ServiceSet, User], Awaitable[T]]
) -> Callable[[web.Request, ServiceSet], Awaitable[T]]:
    MISSING_HEADER = json.dumps({"error": "missing Authentication header"})
    REVOKED = json.dumps({"error": "token was revoked"})

    @functools.wraps(handler)
    async def wrapped(request: web.Request, services: ServiceSet) -> T:
        jwt = request.headers.get("Authentication")
        if not jwt:
            raise web.HTTPForbidden(
                text=MISSING_HEADER, content_type="application/json"
            )
        session = await services.auth.resolve_token(jwt)
        if session.closed:
            raise web.HTTPForbidden(
                text=REVOKED, content_type="application/json"
            )
        user = session.auth.user
        return await handler(request, services, user)
    return wrapped


def wrap_api_response(
    handler: Callable[P, Awaitable[APIResponse]],
    dumps: typedefs.JSONEncoder = DEFAULT_JSON_DUMPER
) -> Callable[P, Awaitable[web.StreamResponse]]:
    @functools.wraps(handler)
    async def wrapped(*args: P.args, **kwargs: P.kwargs) -> web.StreamResponse:
        response: web.StreamResponse
        try:
            api_response = await handler(*args, **kwargs)
        except APIError as api_exc:
            api_response = api_exc
        except ServiceError as service_exc:
            exc_info = APIError.from_service_exc(service_exc)
            api_response = exc_info
        if isinstance(api_response.payload, AsyncIterable):
            response = web.StreamResponse(
                status=api_response.status_code,
                reason=api_response.reason,
                headers=api_response.headers
            )
            async for chunk in api_response.payload:
                await response.write(chunk)
        elif isinstance(api_response.payload, Queue):
            request = web.Request()
            events_response = sse_response(
                request,
                status=api_response.status_code,
                reason=api_response.reason,
                headers=api_response.headers
            )
            events_queue = api_response.payload
            async with events_response as response:
                while True:
                    try:
                        # may be CancelledError if connection was aborted
                        event = await events_queue.get()
                    except asyncio.CancelledError:
                        break
                    body = event.as_json()
                    event_kind = event.__class__.__name__
                    events_response.send(body, event=event_kind)
        else:
            response = web.json_response(
                api_response.payload,
                status=api_response.status_code,
                reason=api_response.reason,
                dumps=dumps,
                headers=api_response.headers
            )
        return response
    return wrapped


def authenticated_handler(
    handler: APIHandler | AuthenticatedHandler, access_level: AccessLevel
) -> TypeGuard[AuthenticatedHandler]:
    ALLOWED = [AccessLevel.USER, AccessLevel.MODERATOR, AccessLevel.ADMIN]
    return access_level in ALLOWED


def default_handler(
    handler: APIHandler | AuthenticatedHandler, access_level: AccessLevel
) -> TypeGuard[APIHandler]:
    return access_level is AccessLevel.ANY
