from __future__ import annotations

from abc import ABC
from contextlib import asynccontextmanager

from typing import AsyncGenerator, Iterable, List, TypeVar, overload

from microchat.core.entities import Bot, Conference, User, Actor, Session
from microchat.core.entities import ConferenceParticipation, Dialog
from microchat.core.entities import Permissions
from microchat.core.entities import FileInfo, Message, Image, Media, TempFile
from microchat.core.jwt_manager import JWTManager
from microchat.storages import UoW


M = TypeVar("M", bound=Media)

Agent = User | Bot | Conference
A = TypeVar("A", bound=Agent)


class ServiceError(ABC, Exception):
    pass


class AccessDenied(ServiceError):
    pass


class AuthenticationError(ServiceError):
    pass


class InvalidCredentials(AuthenticationError):
    pass


class UnsupportedMethod(AuthenticationError):
    pass


class InvalidToken(AuthenticationError):
    pass


class ImageExpected(ServiceError):
    pass


class ServiceSet:

    auth: Auth
    chats: Chats
    conferences: Conferences
    files: Files
    agents: Agents

    def __init__(self, uow: UoW) -> None:
        pass


class Service(ABC):
    uow: UoW

    def __init__(self, uow: UoW) -> None:
        super().__init__()
        self.uow = uow


class Auth(Service):
    jwt_manager: JWTManager

    async def new_session(self, username: str, password: str) -> str:
        entity = await self.uow.entities.get_by_alias(username)
        if not isinstance(entity, User):
            raise InvalidCredentials()
        auth_info = await self.uow.auth.get_auth_data(entity, "password")
        try:
            auth_succeed = auth_info.check(password.encode())
        except NotImplementedError as e:
            raise UnsupportedMethod(e.args[0])
        if not auth_succeed:
            raise InvalidCredentials()
        session = await self.uow.auth.create_session(entity, auth_info)
        token = self.jwt_manager.create_access_token(entity.id, session.id)
        return token

    async def list_sessions(
        self, user: User, offset: int, count: int
    ) -> List[Session]:
        return list(await user.sessions[offset:offset+count])

    async def get_session(self, user: User, id: int) -> Session:
        session = await user.sessions[id]
        return session

    async def resolve_token(self, token: str) -> Session:
        payload = self.jwt_manager.decode_access_token(token)
        entity = await self.uow.entities.get_by_id(payload["user"])
        if not isinstance(entity, User):
            raise InvalidToken()
        session = await entity.sessions[payload["session"]]
        return session

    async def resolve_media_token(
        self, media_cookie: str, csrf_token: str
    ) -> Session:
        session_info = self.jwt_manager.decode_access_token(media_cookie)
        csrf_info = self.jwt_manager.decode_csrf_token(csrf_token)
        # TODO: add CSRF token checking
        entity = self.uow.entities.get_by_id(session_info["user"])
        if not isinstance(entity, User):
            raise InvalidToken()
        session = await entity.sessions[session_info["session"]]
        return session

    async def terminate_session(self, user: User, session: Session) -> None:
        await self.uow.auth.terminate_session(user, session)


class Agents(Service):

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


class Chats(Service):

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


class Conferences(Service):

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


class Files(Service):

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
