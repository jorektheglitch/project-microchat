from __future__ import annotations
from asyncio import Queue

from dataclasses import dataclass
from enum import StrEnum
from typing import AsyncIterable, Generic, Sequence, TypeAlias

from aiohttp import web
from microchat.api_utils.response import APIResponse
from microchat.core.entities import Entity
from microchat.core.events import Event
from microchat.services import ServiceSet

from .types import Executor, Parser, Presenter
from .types import WrappedHandler
from .types import ExtRequest, ExtResponse
from .types import Request, Response, Requirements
from .types import Context
from .types import Factory


class HTTPMethod(StrEnum):
    GET = 'GET'
    POST = 'POST'
    PATCH = 'PATCH'
    DELETE = 'DELETE'


@dataclass
class Route(Generic[Request, *Requirements, Response]):
    path: str
    method: HTTPMethod
    handler: InternalHandler[web.Request, Request, *Requirements, Response, web.Response]


@dataclass(frozen=True)
class InternalHandler(Generic[ExtRequest, Request, *Requirements, Response, ExtResponse]):
    executor: Executor[Request, *Requirements, Response]
    parser: Parser[ExtRequest, Request]
    presenter: Presenter[ExtRequest, Response, ExtResponse] | None = None

    def configure(
        self,
        ctx_factory: Factory[Context[*Requirements]],
        error_presenter: Presenter[ExtRequest, Exception, ExtResponse],
        presenter: Presenter[ExtRequest, Response, ExtResponse] | None = None
    ) -> WrappedHandler[ExtRequest, Request, *Requirements, Response, ExtResponse]:
        presenter = presenter or self.presenter
        if presenter is None:
            raise RuntimeError('presenter must be not None')
        return WrappedHandler(
            executor=self.executor,
            ctx_factory=ctx_factory,
            parser=self.parser,
            presenter=presenter,
            error_presenter=error_presenter
        )


APIRoute: TypeAlias = Route[Request, ServiceSet, APIResponse[str | None | Entity | Sequence[Entity] | AsyncIterable[bytes] | Queue[Event]]]
