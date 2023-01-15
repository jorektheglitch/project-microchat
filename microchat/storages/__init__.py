from __future__ import annotations

from types import TracebackType
from typing import TypeVar, overload

from .bases import AuthenticationStorage
from .bases import EntitiesStorage
from .bases import RelationsStorage
from .bases import ChatsStorage
from .bases import ConferencesStorage
from .bases import MediaStorage
from .bases import EventsManager


T = TypeVar("T")


class UoW:

    auth: AuthenticationStorage
    entities: EntitiesStorage
    events: EventsManager
    relations: RelationsStorage
    chats: ChatsStorage
    conferences: ConferencesStorage
    media: MediaStorage

    async def __aenter__(self: T) -> T:
        return self

    @overload
    async def __aexit__(
        self,
        exc_type: type[BaseException], exc: BaseException, tb: TracebackType
    ) -> None: ...
    @overload
    async def __aexit__(self, exc_type: None, exc: None, tb: None) -> None: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None
    ) -> None:
        pass
