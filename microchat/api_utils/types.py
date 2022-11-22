from __future__ import annotations

from typing import Awaitable, Callable, Sequence

from aiohttp import web

from microchat.services import ServiceSet
from microchat.core.entities import Entity, User

from .exceptions import APIError
from .request import APIRequest
from .response import APIResponse, APIResponseEncoder


JSON = str | int | float | list["JSON"] | dict[str, "JSON"] | None
APIResponseBody = Entity | Sequence[Entity] | dict[str, Entity]


Handler = Callable[
    [web.Request],
    Awaitable[web.StreamResponse]
]

APIHandler = Callable[
    [web.Request, ServiceSet],
    Awaitable[APIResponse]
]
AuthenticatedHandler = Callable[
    [web.Request, ServiceSet, User],
    Awaitable[APIResponse]
]
Middleware = Callable[
    [web.Request, Handler],
    Awaitable[web.StreamResponse]
]
