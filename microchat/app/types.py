from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, AsyncContextManager, Generic, TypeAlias, TypeVar, TypeVarTuple


T = TypeVar("T")

ExtRequest = TypeVar("ExtRequest", contravariant=True)
ExtResponse = TypeVar("ExtResponse", covariant=True)
Request = TypeVar("Request", contravariant=True)
Response = TypeVar("Response", covariant=True)
Requirements = TypeVarTuple("Requirements")


ExtHandler: TypeAlias = Callable[[ExtRequest], Awaitable[ExtResponse]]

Parser: TypeAlias = Callable[[ExtRequest], Awaitable[Request]]
Executor: TypeAlias = Callable[[Request, *Requirements], Awaitable[Response]]
Presenter: TypeAlias = Callable[[ExtRequest, Response], Awaitable[ExtResponse]]

Factory: TypeAlias = Callable[[], T]

Context: TypeAlias = AsyncContextManager[tuple[*Requirements]]


@dataclass
class Handler(Generic[Request, *Requirements, Response]):
    executor: Executor[Request, *Requirements, Response]
    ctx_factory: Factory[Context[*Requirements]]

    def wrap(
        self,
        parser: Parser[ExtRequest, Request],
        presenter: Presenter[ExtRequest, Response, ExtResponse],
        error_presenter: Presenter[ExtRequest, Exception, ExtResponse],
    ) -> WrappedHandler[ExtRequest, Request, *Requirements, Response, ExtResponse]:
        return WrappedHandler(
            executor=self.executor,
            ctx_factory=self.ctx_factory,
            parser=parser,
            presenter=presenter,
            error_presenter=error_presenter
        )


@dataclass
class WrappedHandler(Handler[Request, *Requirements, Response], Generic[ExtRequest, Request, *Requirements, Response, ExtResponse]):
    executor: Executor[Request, *Requirements, Response]
    ctx_factory: Factory[Context[*Requirements]]
    parser: Parser[ExtRequest, Request]
    presenter: Presenter[ExtRequest, Response, ExtResponse]
    error_presenter: Presenter[ExtRequest, Exception, ExtResponse]

    async def __call__(self, ext_request: ExtRequest) -> ExtResponse:
        async with self.ctx_factory() as ctx:
            try:
                request = await self.parser(ext_request)
                result = await self.executor(request, *ctx)
                ext_response = await self.presenter(ext_request, result)
            except Exception as exc:
                ext_response = await self.error_presenter(ext_request, exc)
            return ext_response

    def unwrap(self) -> Handler[Request, *Requirements, Response]:
        return Handler(self.executor, self.ctx_factory)
