from __future__ import annotations

from contextlib import asynccontextmanager

from typing import AsyncGenerator, Iterable, List, TypeVar, overload

from microchat.core.entities import Bot, Conference, User, Actor, Session
from microchat.core.entities import ConferenceParticipation, Dialog
from microchat.core.entities import Permissions
from microchat.core.entities import FileInfo, Message, Image, Media, TempFile
from microchat.storages import UoW


M = TypeVar("M", bound=Media)

Agent = User | Bot | Conference
A = TypeVar("A", bound=Agent)


class ServiceError(Exception):
    pass


class ServiceSet:

    auth: Auth
    chats: Chats
    conferences: Conferences
    files: Files
    agents: Agents

    def __init__(self, uow: UoW) -> None:
        pass


class Auth:

    async def new_session(self, username: str, password: str) -> str:
        pass

    async def list_sessions(self, user: User, offset: int, count: int) -> List[Session]:
        pass

    async def get_session(self, user: User, id: int) -> Session:
        pass

    async def resolve_token(self, token: str) -> Session:
        pass

    async def resolve_media_token(self, auth_cookie: str) -> Session:
        pass

    async def check_csrf_token(self, user: User, csrf_token: str) -> bool:
        pass

    async def terminate_session(self, user: User, session: Session) -> None:
        pass


class Agents:

    async def get(
        self, user: User, id: int
    ) -> Agent:
        pass

    async def resolve_alias(
        self, user: User, alias: str
    ) -> Agent:
        pass

    async def get_chat(
        self, user: User, id: int
    ) -> Dialog | ConferenceParticipation[User]:
        pass

    async def resolve_chat_alias(
        self, user: User, alias: str
    ) -> Dialog | ConferenceParticipation[User]:
        pass

    async def list_avatars(
        self, user: User, agent: Agent, offset: int, count: int
    ) -> List[Image]:
        pass

    async def get_avatar(
        self, user: User, agent: Agent, id: int
    ) -> Image:
        pass

    async def edit_self(
        self,
        user: User,
        alias: str | None = None,
        avatar: str | None = None,
        name: str | None = None,
        surname: str | None = None,
        bio: str | None = None
    ) -> User:
        pass

    async def edit_permissions(
        self,
        user: User,
        relation: Dialog,
        **kwargs: bool
    ) -> Dialog:
        pass

    async def edit_agent(
        self,
        user: User,
        agent: A,
        **kwargs: str
    ) -> A:
        # raise is user != agent
        pass

    async def set_avatar(
        self, user: User, agent: Agent, avatar: Image
    ) -> None:
        pass

    async def remove_avatar(
        self, user: User, agent: Agent, id: int
    ) -> None:
        pass

    async def remove_agent(self, user: User, agent: Agent) -> None:
        pass


class Chats:

    async def list_chats(
        self, user: User, offset: int, count: int
    ) -> List[Dialog | ConferenceParticipation[User]]:
        pass

    async def remove_chat(
        self, user: User, chat: Dialog | ConferenceParticipation[User]
    ) -> None:
        pass

    async def list_chat_messages(
        self,
        user: User, chat: Dialog | ConferenceParticipation[User],
        offset: int, count: int
    ) -> List[Message]:
        pass

    async def get_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User], id: int
    ) -> Message:
        pass

    @overload
    async def add_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        text: str, attachments: None, reply_to: Message | None
    ) -> Message: ...
    @overload
    async def add_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        text: str, attachments: List[Media], reply_to: Message | None
    ) -> Message: ...
    @overload
    async def add_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        text: None, attachments: List[Media], reply_to: Message | None
    ) -> Message: ...

    async def add_chat_message(
        self,
        user: User,
        chat: Dialog | ConferenceParticipation[User],
        text: str | None = None,
        attachments: List[Media] | None = None,
        reply_to: Message | None = None
    ) -> Message:
        pass


    @overload
    async def edit_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        id: int, text: str, attachments: None
    ) -> Message: ...
    @overload
    async def edit_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        id: int, text: str, attachments: List[Media]
    ) -> Message: ...
    @overload
    async def edit_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        id: int, text: None, attachments: List[Media]
    ) -> Message: ...

    async def edit_chat_message(
        self,
        user: User,
        chat: Dialog | ConferenceParticipation[User],
        id: int,
        text: str | None = None,
        attachments: List[Media] | None = None
    ) -> Message:
        pass

    async def remove_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User], id: int
    ) -> None:
        pass

    async def list_chat_media(
        self,
        user: User, chat: Dialog | ConferenceParticipation[User],
        media_type: type[M],
        offset: int, count: int
    ) -> List[M]:
        pass

    async def get_chat_media(
        self,
        user: User, chat: Dialog | ConferenceParticipation[User],
        media_type: type[M],
        id: int
    ) -> Media:
        pass

    async def remove_chat_media(
        self,
        user: User, chat: Dialog | ConferenceParticipation[User],
        media_type: type[M],
        id: int
    ) -> None:
        pass


class Conferences:

    async def list_chat_members(
        self, user: User | Bot, conference: Conference,
        offset: int, count: int
    ) -> List[ConferenceParticipation[User | Bot]]:
        pass

    async def get_chat_member(
        self, user: User | Bot, conference: Conference,
        no: int | User | Bot
    ) -> ConferenceParticipation[User | Bot]:
        pass

    async def add_chat_member(
        self, user: User, conference: Conference,
        invitee: Actor
    ) -> ConferenceParticipation[Actor]:
        pass

    async def remove_chat_member(
        self, user: User, conference: Conference,
        id: int | User | Bot
    ) -> None:
        pass

    async def get_chat_member_permissions(
        self, user: User | Bot, conference: Conference,
        no: int | User | Bot
    ) -> Permissions:
        pass

    async def edit_chat_member_permissions(
        self, user: User | Bot, conference: Conference,
        no: int | User | Bot,
        read: bool | None = None,
        send: bool | None = None,
        delete: bool | None = None,
        send_media: bool | None = None,
        send_mediamessage: bool | None = None,
        add_user: bool | None = None,
        pin_message: bool | None = None,
        edit_conference: bool | None = None,
    ) -> Permissions:
        pass


class Files:

    async def materialize(
        self,
        user: User,
        file: TempFile,
        name: str,
        mime_type: str
    ) -> Media:
        pass

    async def get_info(self, user: User, hash: str) -> Media:
        pass

    async def get_infos(self, user: User, ids: Iterable[int]) -> List[Media]:
        pass

    async def iter_content(
        self,
        user: User,
        file: FileInfo,
        *,
        chunk_size: int = 1024**2
    ) -> AsyncGenerator[bytes, None]:
        yield

    @asynccontextmanager
    async def tempfile(self) -> AsyncGenerator[TempFile, None]:
        tmpfile: TempFile
        try:
            yield tmpfile
        finally:
            await tmpfile.close()
