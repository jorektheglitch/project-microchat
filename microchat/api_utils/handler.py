from __future__ import annotations

import functools

from typing import TypeVar
from typing import Awaitable, Callable
from typing import TYPE_CHECKING

from microchat.api_utils.exceptions import Unauthorized
from microchat.api_utils.types import APIHandler, Handler
from microchat.core.jwt_manager import JWTManager
from microchat.core.entities import User
from microchat.services import ServiceSet
from microchat.storages import UoW

if TYPE_CHECKING:
    from .types import AuthenticatedHandler
    from .types import R, AR, CAR

from .response import APIResponse, P


T = TypeVar("T")


def authenticated(
    handler: Callable[[AR, ServiceSet, User], Awaitable[APIResponse[P]]]
) -> AuthenticatedHandler[AR, P]:
    MISSING_HEADER = "Missing access token"
    REVOKED = "Token was revoked"

    @functools.wraps(handler)
    async def wrapped(
        request: AR, services: ServiceSet, user: User | None = None
    ) -> APIResponse[P]:
        if user is None:
            jwt = request.access_token
            if not jwt:
                raise Unauthorized(MISSING_HEADER)
            session = await services.auth.resolve_token(jwt)
            if session.closed:
                raise Unauthorized(REVOKED)
            user = session.auth.user
        return await handler(request, services, user)
    return wrapped


def cookie_authenticated(
    handler: Callable[[CAR, ServiceSet, User], Awaitable[APIResponse[P]]]
) -> AuthenticatedHandler[CAR, P]:
    REVOKED = "Token was revoked"

    @functools.wraps(handler)
    async def wrapped(
        request: CAR, services: ServiceSet, user: User | None = None
    ) -> APIResponse[P]:
        if user is None:
            auth_cookie = request.access_token
            csrf_token = request.csrf_token
            session = await services.auth.resolve_media_token(
                auth_cookie, csrf_token
            )
            if session.closed:
                raise Unauthorized(REVOKED)
            user = session.auth.user
        return await handler(request, services, user)
    return wrapped


def services_injector(
    uow_factory: Callable[[], UoW],
    jwt_manager: JWTManager
) -> Callable[[Handler[R, P]], APIHandler[R, P]]:
    def with_services(
        executor: Handler[R, P]
    ) -> APIHandler[R, P]:
        return inject_services(executor, uow_factory, jwt_manager)
    return with_services


def inject_services(
    executor: Handler[R, P],
    uow_factory: Callable[[], UoW],
    jwt_manager: JWTManager
) -> APIHandler[R, P]:
    async def with_services(request: R) -> APIResponse[P]:
        async with uow_factory() as uow:
            services = ServiceSet(uow, jwt_manager)
            response = await executor(request, services)
        return response
    return with_services
