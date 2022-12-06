from __future__ import annotations

from typing import Awaitable, Callable, Generic, Protocol, TypeVar

from microchat.services import ServiceSet
from microchat.core.entities import User

from .exceptions import APIError  # noqa: F401
from .request import APIRequest, Authenticated
from .response import APIResponse, APIResponseEncoder, JSON  # noqa: F401


T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
R = TypeVar("R", bound=APIRequest, contravariant=True)
AR = TypeVar("AR", bound=Authenticated, contravariant=True)


class AuthenticatedHandler(Protocol, Generic[AR, T_co]):
    async def __call__(
        self, request: AR, services: ServiceSet, user: User | None = None
    ) -> T_co:
        pass


APIHandler = Callable[
    [APIRequest],
    Awaitable[APIResponse[T]]
]
