from __future__ import annotations

from typing import List, NewType

from microchat.core.entities import Bot, Conference, Dialog, File, User, Session, Image, Media
from microchat.storages import UoW


class ServiceError(Exception):
    pass


class ServiceSet:

    auth: Authentication
    chats: Chats
    files: Files

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


class Chats:

    async def list_chats(
        self, user: User, offset: int, count: int
    ) -> List[Dialog | Conference]:
        pass

    async def resolve_alias(
        self, user: User, alias: str
    ) -> Dialog | Conference:
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
