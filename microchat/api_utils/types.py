from __future__ import annotations

from asyncio import Queue

from typing import AsyncIterable, Protocol, TypeVar

from microchat.core.events import Event
from microchat.core.entities import User
from microchat.services import ServiceSet

from .exceptions import APIError  # noqa: F401
from .request import APIRequest, AuthenticatedRequest, CookieAuthenticatedRequest
from .response import APIResponse, APIResponseEncoder  # noqa: F401
from .response import APIResponseBody, JSON


T = TypeVar("T")
P = TypeVar("P", bound=APIResponseBody | JSON | AsyncIterable[bytes] | Queue[Event], covariant=True)
R = TypeVar("R", bound=APIRequest, contravariant=True)
AR = TypeVar("AR", bound=AuthenticatedRequest, contravariant=True)
CAR = TypeVar("CAR", bound=CookieAuthenticatedRequest, contravariant=True)


class APIHandler(Protocol[R, P]):
    async def __call__(
        self, request: R
    ) -> APIResponse[P]:
        pass


class Handler(Protocol[R, P]):
    async def __call__(
        self, request: R, services: ServiceSet
    ) -> APIResponse[P]:
        pass


class AuthenticatedHandler(Handler[AR, P], Protocol[AR, P]):
    async def __call__(
        self, request: AR, services: ServiceSet, user: User | None = None
    ) -> APIResponse[P]:
        pass
