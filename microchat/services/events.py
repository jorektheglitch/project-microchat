from asyncio import Queue
from functools import wraps

from typing import Awaitable, Callable, Concatenate, ParamSpec, TypeVar

from microchat.core.entities import User, Bot
from microchat.core.events import Event

from .base_service import Service


Params = ParamSpec("Params")
Returns = TypeVar("Returns", covariant=True)
Svc = TypeVar("Svc", bound=Service)


def event_emitter(event_type: type[Event]) -> Callable[[Callable[Concatenate[Svc, Params], Awaitable[Returns]]], Callable[Concatenate[Svc, Params], Awaitable[Returns]]]:
    def wrapper(
        method: Callable[Concatenate[Svc, Params], Awaitable[Returns]]
    ) -> Callable[Concatenate[Svc, Params], Awaitable[Returns]]:
        @wraps(method)
        async def wrapped(self: Svc, /, *args: Params.args, **kwargs: Params.kwargs) -> Returns:
            result = await method(self, *args, **kwargs)
            await self.uow.events.emit(event_type())
            return result
        return wrapped
    return wrapper


class Events(Service):

    async def get_event_stream(self, actor: User | Bot) -> Queue[Event]:
        return await self.uow.events.get_event_stream(actor)
