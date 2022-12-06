from __future__ import annotations

import functools

from typing import TypeVar
from typing import Awaitable, Callable
from typing import TYPE_CHECKING

from microchat.api_utils.exceptions import Unauthorized
from microchat.core.jwt_manager import JWTManager
from microchat.core.entities import User
from microchat.services import ServiceSet
from microchat.storages import UoW

if TYPE_CHECKING:
    from .types import AuthenticatedHandler
    from .types import R, AR

from .response import APIResponse, P


T = TypeVar("T")


def authenticated(
    handler: Callable[[AR, ServiceSet, User], Awaitable[T]]
) -> AuthenticatedHandler[AR, T]:
    MISSING_HEADER = "Missing access token"
    REVOKED = "Token was revoked"

    @functools.wraps(handler)
    async def wrapped(
        request: AR, services: ServiceSet, user: User | None = None
    ) -> T:
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


def services_injector(
    uow_factory: Callable[[], UoW],
    jwt_manager: JWTManager
) -> Callable[[Callable[[R, ServiceSet], Awaitable[APIResponse[P]]]], Callable[[R], Awaitable[APIResponse[P]]]]:
    def inject_services(
        executor: Callable[[R, ServiceSet], Awaitable[APIResponse[P]]]
    ) -> Callable[[R], Awaitable[APIResponse[P]]]:
        async def with_services(request: R) -> APIResponse[P]:
            async with uow_factory() as uow:
                services = ServiceSet(uow)
                response = await executor(request, services)
            return response
        return with_services
    return inject_services


def inject_services(
    executor: Callable[[R, ServiceSet], Awaitable[APIResponse[P]]],
    uow_factory: Callable[[], UoW],
    jwt_manager: JWTManager
) -> Callable[[R], Awaitable[APIResponse[P]]]:
    async def with_services(request: R) -> APIResponse[P]:
        async with uow_factory() as uow:
            services = ServiceSet(uow)
            response = await executor(request, services)
        return response
    return with_services
