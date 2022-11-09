from __future__ import annotations

from abc import ABC
import enum
import json
import functools
from dataclasses import dataclass

from typing import Any, Awaitable, Callable, ClassVar, Literal, Sequence, TypeGuard
from typing import overload

from aiohttp import web

from microchat.services import ServiceError, ServiceSet, AccessToken
from microchat.core.entities import Entity, User


JSON = str | int | float | list["JSON"] | dict[str, "JSON"] | None
APIResponseBody = Entity | Sequence[Entity] | dict[str, Entity]


class APIException(ABC, Exception):
    status_code: ClassVar[int]
    payload: JSON
    reason: str | None

    def __init__(
        self,
        msg: str | None = None,
        *,
        payload: JSON = None,
        reason: str | None = None
    ) -> None:
        super().__init__(msg)
        if payload is None and msg is not None:
            self.payload = {"error": msg}
        else:
            self.payload = payload
        self.reason = reason

    @classmethod
    def from_service_exc(cls, exc: ServiceError) -> APIException:
        pass


class BadRequest(APIException):
    status_code = 400


class Unauthorized(APIException):
    status_code = 401


class Forbidden(APIException):
    status_code = 403


class NotFound(APIException):
    status_code = 404


class HTTPStatus(enum.Enum):
    OK = 200
    CREATED = 201
    NO_CONTENT = 204


@dataclass
class APIResponse:
    payload: dict[str, APIResponseBody | JSON]
    status: HTTPStatus = HTTPStatus.OK

    def __init__(
        self,
        payload: APIResponseBody | JSON = None,
        status: HTTPStatus = HTTPStatus.OK
    ) -> None:
        self.payload = {"response": payload}
        self.status = status

    @property
    def status_code(self) -> int:
        return self.status.value


class APIResponseEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:  # type: ignore  # Any not allowed
        if isinstance(o, Entity):
            # TODO: make serialization for all entity types
            pass
        return super().default(o)


Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]

APIHandler = Callable[[web.Request, ServiceSet], Awaitable[APIResponse]]
AuthenticatedHandler = Callable[[web.Request, ServiceSet, User], Awaitable[APIResponse]]
Middleware = Callable[[web.Request, Handler], Awaitable[web.StreamResponse]]


class AccessLevel(enum.Enum):
    ANY = enum.auto()
    USER = enum.auto()
    MODERATOR = enum.auto()
    ADMIN = enum.auto()


@overload
def api_handler() -> Callable[[AuthenticatedHandler], Callable[[web.Request], Awaitable[web.StreamResponse]]]: ...
@overload
def api_handler(
    access_level: Literal[AccessLevel.ANY],
    *,
    encoder: type[json.JSONEncoder] = APIResponseEncoder
) -> Callable[[APIHandler], Callable[[web.Request], Awaitable[web.StreamResponse]]]: ...
@overload
def api_handler(
    access_level: Literal[AccessLevel.USER, AccessLevel.MODERATOR, AccessLevel.ADMIN] = AccessLevel.USER,
    *,
    encoder: type[json.JSONEncoder] = APIResponseEncoder
) -> Callable[[AuthenticatedHandler], Callable[[web.Request], Awaitable[web.StreamResponse]]]: ...
@overload
def api_handler(
    handler: APIHandler,
    access_level: Literal[AccessLevel.ANY],
    *,
    encoder: type[json.JSONEncoder] = APIResponseEncoder
) -> Callable[[web.Request], Awaitable[web.StreamResponse]]: ...
@overload
def api_handler(
    handler: AuthenticatedHandler
) -> Callable[[web.Request], Awaitable[web.StreamResponse]]: ...
@overload
def api_handler(
    handler: AuthenticatedHandler,
    access_level: Literal[AccessLevel.USER, AccessLevel.MODERATOR, AccessLevel.ADMIN] = AccessLevel.USER,
    *,
    encoder: type[json.JSONEncoder] = APIResponseEncoder
) -> Callable[[web.Request], Awaitable[web.StreamResponse]]: ...

def api_handler(  # noqa
    handler: APIHandler | AuthenticatedHandler | None = None,
    access_level: AccessLevel = AccessLevel.USER,
    *,
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

    @functools.wraps(handler)
    async def wrapped_handler(request: web.Request) -> web.StreamResponse:
        services: ServiceSet = request["services"]
        if default_handler(handler, access_level):
            try:
                api_response = await handler(request, services)
            except APIException as api_exc:
                response = web.json_response(
                    api_exc.payload,
                    status=api_exc.status_code,
                    reason=api_exc.reason,
                    dumps=dumps
                )
            except ServiceError as service_exc:
                api_exc = APIException.from_service_exc(service_exc)
                response = web.json_response(
                    api_exc.payload,
                    status=api_exc.status_code,
                    reason=api_exc.reason,
                    dumps=dumps
                )
            else:
                response = web.json_response(
                    api_response.payload,
                    status=api_response.status_code,
                    dumps=dumps
                )
        elif authenticated_handler(handler, access_level):
            token_raw = request.headers.get("Authentication")
            if not token_raw:
                return web.json_response(
                    {"error": "missing Authentication header"},
                    status=403
                )
            token = AccessToken(token_raw)
            session = await services.auth.resolve_token(token)
            user = session.auth.user
            try:
                api_response = await handler(request, services, user)
            except APIException as api_exc:
                response = web.json_response(
                    api_exc.payload,
                    status=api_exc.status_code,
                    reason=api_exc.reason,
                    dumps=dumps
                )
            except ServiceError as service_exc:
                api_exc = APIException.from_service_exc(service_exc)
                response = web.json_response(
                    api_exc.payload,
                    status=api_exc.status_code,
                    reason=api_exc.reason,
                    dumps=dumps
                )
            else:
                response = web.json_response(
                    api_response.payload,
                    status=api_response.status_code,
                    dumps=dumps
                )
        else:
            raise web.HTTPBadRequest()
        return response
    return wrapped_handler


def authenticated_handler(
    handler: APIHandler | AuthenticatedHandler, access_level: AccessLevel
) -> TypeGuard[AuthenticatedHandler]:
    ALLOWED = [AccessLevel.USER, AccessLevel.MODERATOR, AccessLevel.ADMIN]
    return access_level in ALLOWED


def default_handler(
    handler: APIHandler | AuthenticatedHandler, access_level: AccessLevel
) -> TypeGuard[APIHandler]:
    return access_level is AccessLevel.ANY
