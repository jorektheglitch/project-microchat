from __future__ import annotations

from typing import Iterable, List, NewType, TypeVar, overload

from microchat.core.entities import Bot, Conference, User, Session
from microchat.core.entities import ConferenceBot, ConferenceMember, Dialog
from microchat.core.entities import Permissions
from microchat.core.entities import File, Message, Image, Media
from microchat.storages import UoW


M = TypeVar("M", bound=Media)


class ServiceError(Exception):
    pass


class ServiceSet:

    auth: Authentication
    chats: Chats
    conferences: Conferences
    files: Files
    agents: Agents

    def __init__(self, uow: UoW) -> None:
        pass


AccessToken = NewType("AccessToken", str)


class Authentication:

    async def new_session(self, username: str, password: str) -> AccessToken:
        pass

    async def list_sessions(self, user: User, offset: int, count: int) -> List[Session]:
        pass

    async def resolve_token(self, access_token: AccessToken) -> Session:
        pass

    async def terminate_session(self, user: User, session: Session) -> None:
        pass


class Agents:

    async def get(
        self, user: User, id: int
    ) -> User | Bot | Conference:
        pass

    async def resolve_alias(
        self, user: User, alias: str
    ) -> User | Bot | Conference:
        pass

    async def resolve_chat_alias(
        self, user: User, alias: str
    ) -> Dialog | Conference:
        pass


class Chats:

    async def list_chats(
        self, user: User, offset: int, count: int
    ) -> List[Dialog | Conference]:
        pass

    async def remove_chat(
        self, user: User, chat: Dialog | Conference
    ) -> None:
        pass

    async def list_chat_avatars(
        self, user: User, chat: Dialog | Conference, offset: int, count: int
    ) -> List[Image]:
        pass

    async def set_chat_avatar(
        self, user: User, chat: Dialog | Conference, avatar: Image
    ) -> None:
        pass

    async def remove_chat_avatar(
        self, user: User, chat: Dialog | Conference, id: int
    ) -> None:
        pass

    async def list_chat_messages(
        self, user: User, chat: Dialog | Conference, offset: int, count: int
    ) -> List[Message]:
        pass

    async def get_chat_message(
        self, user: User, chat: Dialog | Conference, id: int
    ) -> Message:
        pass

    @overload
    async def add_chat_message(
        self, user: User, chat: Dialog | Conference,
        text: str, attachments: None, reply_to: Message | None
    ) -> Message: ...
    @overload
    async def add_chat_message(
        self, user: User, chat: Dialog | Conference,
        text: str, attachments: List[Media], reply_to: Message | None
    ) -> Message: ...
    @overload
    async def add_chat_message(
        self, user: User, chat: Dialog | Conference,
        text: None, attachments: List[Media], reply_to: Message | None
    ) -> Message: ...

    async def add_chat_message(
        self,
        user: User,
        chat: Dialog | Conference,
        text: str | None = None,
        attachments: List[Media] | None = None,
        reply_to: Message | None = None
    ) -> Message:
        pass


    @overload
    async def edit_chat_message(
        self, user: User, chat: Dialog | Conference, id: int,
        text: str, attachments: None
    ) -> Message: ...
    @overload
    async def edit_chat_message(
        self, user: User, chat: Dialog | Conference, id: int,
        text: str, attachments: List[Media]
    ) -> Message: ...
    @overload
    async def edit_chat_message(
        self, user: User, chat: Dialog | Conference, id: int,
        text: None, attachments: List[Media]
    ) -> Message: ...

    async def edit_chat_message(
        self,
        user: User,
        chat: Dialog | Conference,
        id: int,
        text: str | None = None,
        attachments: List[Media] | None = None
    ) -> Message:
        pass

    async def remove_chat_message(
        self, user: User, chat: Dialog | Conference, id: int
    ) -> None:
        pass

    async def list_chat_media(
        self,
        user: User, chat: Dialog | Conference, media_type: type[M],
        offset: int, count: int
    ) -> List[M]:
        pass

    async def get_chat_media(
        self,
        user: User, chat: Dialog | Conference, media_type: type[M],
        id: int
    ) -> Media:
        pass

    async def remove_chat_media(
        self,
        user: User, chat: Dialog | Conference, media_type: type[M],
        id: int
    ) -> None:
        pass


class Conferences:

    async def list_chat_members(
        self, user: User | Bot, conference: Conference,
        offset: int, count: int
    ) -> List[ConferenceBot | ConferenceMember]:
        pass

    async def get_chat_member(
        self, user: User | Bot, conference: Conference,
        no: int | User | Bot
    ) -> ConferenceBot | ConferenceMember:
        pass

    @overload
    async def add_chat_member(
        self, user: User, conference: Conference,
        invitee: User
    ) -> ConferenceMember: ...
    @overload
    async def add_chat_member(
        self, user: User, conference: Conference,
        invitee: Bot
    ) -> ConferenceBot: ...

    async def add_chat_member(
        self, user: User, conference: Conference,
        invitee: User | Bot
    ) -> ConferenceMember | ConferenceBot:
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

    async def store(
        self,
        user: User,
        file: File,
        name: str,
        mime_type: str
    ) -> Media:
        pass

    async def get_info(self, user: User, id: int) -> Media:
        pass

    async def get_infos(self, user: User, ids: Iterable[int]) -> List[Media]:
        pass
