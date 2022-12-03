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
    entities: EntitiesStorage

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


class EntitiesStorage(ABC):

    @abstractmethod
    async def get_by_alias(self, alias: str) -> User | Bot | Conference:
        pass

    @abstractmethod
    async def get_by_id(self, id: int) -> User | Bot | Conference:
        pass

    @abstractmethod
    async def edit_user(
        self,
        user: User,
        alias: str | None = None,
        avatar: Image | None = None,
        name: str | None = None,
        surname: str | None = None,
        bio: str | None = None
    ) -> User:
        pass

    @abstractmethod
    async def edit_entity(
        self, entity: A, update: dict[str, Any]
    ) -> A:
        pass

    @abstractmethod
    async def set_avatar(
        self, entity: Bot | User | Conference, avatar: Image
    ) -> None:
        pass

    @abstractmethod
    async def remove_entity(self, entity: Bot | User | Conference) -> None:
        pass

    @abstractmethod
    async def remove_avatar(
        self, entity: Bot | User | Conference, id: int
    ) -> None:
        pass
