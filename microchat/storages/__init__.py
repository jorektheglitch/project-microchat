from __future__ import annotations

from abc import ABC, abstractmethod

from types import TracebackType
from typing import Any, TypeVar, overload

from microchat.core.entities import Authentication, Session
from microchat.core.entities import User, Bot, Conference, Dialog
from microchat.core.entities import ConferenceParticipation, ConferencePresence
from microchat.core.entities import Message, Attachment
from microchat.core.entities import Media, Image
from microchat.core.types import AsyncSequence


T = TypeVar("T")
A = TypeVar("A", bound=User | Bot | Conference)
M = TypeVar("M", bound=Media)
Exc = TypeVar("Exc", BaseException, Exception)


class UoW:

    auth: AuthenticationStorage

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


class AuthenticationStorage(ABC):

    @abstractmethod
    async def get_auth_data(
        self, user: User, auth_kind: str
    ) -> Authentication:
        pass

    @abstractmethod
    async def create_session(
        self, user: User, auth: Authentication
    ) -> Session:
        pass

    @abstractmethod
    async def terminate_session(self, user: User, session: Session) -> None:
        pass
