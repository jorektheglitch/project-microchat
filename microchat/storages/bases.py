from __future__ import annotations

from abc import ABC, abstractmethod

from typing import Any, Iterable, TypeVar

from microchat.core.entities import Authentication, Permissions, Session
from microchat.core.entities import User, Bot, Conference, Dialog
from microchat.core.entities import ConferenceParticipation, ConferencePresence
from microchat.core.entities import Message, Attachment
from microchat.core.entities import Media, Image, TempFile, FileInfo
from microchat.core.types import AsyncReader, AsyncSequence, MIMETuple


Agent = TypeVar("Agent", bound=User | Bot | Conference)
Actor = TypeVar("Actor", bound=User | Bot)
M = TypeVar("M", bound=Media)
Exc = TypeVar("Exc", BaseException, Exception)


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
        self, entity: Agent, update: dict[str, Any]
    ) -> Agent:
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


class RelationsStorage(ABC):

    @abstractmethod
    async def get_relation(
        self, user: User | Bot, id: int
    ) -> Dialog | ConferenceParticipation[User]:
        pass

    @abstractmethod
    async def edit_permissions(
        self, user: User, relation: Dialog, update: dict[str, bool]
    ) -> Dialog:
        pass


class ChatsStorage(ABC):

    @abstractmethod
    async def get_user_chats(
        self, user: User, offset: int, count: int
    ) -> list[Dialog | ConferenceParticipation[User]]:
        pass

    @abstractmethod
    async def get_dialog_messages(
        self, user: User, chat: Dialog, offset: int, count: int
    ) -> list[Message]:
        pass

    @abstractmethod
    async def get_conference_messages(
        self,
        user: User, chat: ConferenceParticipation[User],
        offset: int, count: int,
    ) -> list[Message]:
        pass

    @abstractmethod
    async def get_private_conference_messages(
        self,
        user: User,
        chat: ConferenceParticipation[User],
        offset: int,
        count: int,
        presences: AsyncSequence[ConferencePresence]
    ) -> list[Message]:
        pass

    @abstractmethod
    async def add_message(
        self,
        user: User, chat: Dialog | ConferenceParticipation[User],
        text: str | None,
        attachments: list[Media] | None,
        reply_to: Message | None
    ) -> Message:
        pass

    @abstractmethod
    async def edit_message(
        self,
        message: Message,
        text: str | None,
        attachments: list[Media] | None
    ) -> Message:
        pass

    @abstractmethod
    async def remove_message(self, message: Message) -> None:
        pass

    @abstractmethod
    async def get_dialog_medias(
        self,
        user: User,
        chat: Dialog,
        media_type: type[M],
        offset: int,
        count: int
    ) -> list[Attachment[M]]:
        pass

    @abstractmethod
    async def get_conference_medias(
        self,
        user: User, chat: ConferenceParticipation[User],
        media_type: type[M],
        offset: int, count: int,
    ) -> list[Attachment[M]]:
        pass

    @abstractmethod
    async def get_private_conference_medias(
        self,
        user: User,
        chat: ConferenceParticipation[User],
        media_type: type[M],
        offset: int,
        count: int,
        presences: AsyncSequence[ConferencePresence]
    ) -> list[Attachment[M]]:
        pass

    @abstractmethod
    async def remove_media(self, attachment: Attachment[M]) -> None:
        pass


class ConferencesStorage(ABC):

    @abstractmethod
    async def list_members(
        self, conference: Conference, offset: int, count: int
    ) -> list[ConferenceParticipation[User | Bot]]:
        pass

    @abstractmethod
    async def find_member(
        self, conference: Conference, actor: Actor
    ) -> ConferenceParticipation[Actor]:
        pass

    @abstractmethod
    async def add_member(
        self, conference: Conference, invitee: Actor
    ) -> ConferenceParticipation[Actor]:
        pass

    @abstractmethod
    async def remove_member(
        self, member: ConferenceParticipation[User | Bot]
    ) -> None:
        pass

    @abstractmethod
    async def update_permissions(
        self, member: ConferenceParticipation[User | Bot], update: Permissions
    ) -> Permissions:
        pass


class MediaStorage(ABC):

    @abstractmethod
    async def get_by_hash(self, user: User, hash: str) -> Media:
        pass

    @abstractmethod
    async def get_by_hashes(
        self, user: User, hashes: Iterable[str]
    ) -> list[Media]:
        pass

    @abstractmethod
    async def save_media(
        self, user: User, file: TempFile, name: str, mime: MIMETuple
    ) -> Media:
        pass

    @abstractmethod
    async def create_tempfile(self) -> TempFile:
        pass

    @abstractmethod
    async def open(self, file: FileInfo) -> AsyncReader:
        pass
