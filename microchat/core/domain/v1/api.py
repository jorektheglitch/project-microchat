"""
Модуль содержащий классы реализующие взаимодействия между сущностями \
(usecase'ы).
"""

from datetime import datetime as dt
from typing import Generic, Iterable, Optional, TypeVar, Union

from repositories import Repository
from .entities import Entity
from .entities import Attachment, Message
from .entities import Conference, Dialog
from .entities import Session, User


E = TypeVar('E', bound=Entity)
M = TypeVar('M', bound=Message)
T = TypeVar('T')


class UsecaseSet(Generic[E]):

    repo: Repository[E]

    def __init__(self, repo: Repository[E]) -> None:
        self.repo = repo


class Sessions(UsecaseSet[Session]):

    def get(self, token: bytes) -> Optional[Session]:
        return self.repo.get(token=token)


class Users(UsecaseSet[User]):

    async def get(self, user_id: int) -> Optional[User]:
        return await self.repo.get(id=user_id)

    async def search(self, username: str) -> Iterable[User]:
        return await self.repo.search(username=username)


class Messages(UsecaseSet[Message]):

    async def get(self, holder: T, no: int) -> Optional[Message[T]]:
        return await self.repo.get(holder=holder, no=no)

    async def create(
        self,
        sender: User,
        receiver: T,
        text: Union[str, bytes],
        attachments: Iterable[Attachment],
        reply_to: Optional[Message[T]]
    ) -> Message[T]:
        return await self.repo.create(
            sender=sender,
            receiver=receiver,
            text=text,
            attachments=attachments,
            time_sent=dt.now,
            time_edit=None,
            reply_to=reply_to
        )

    async def replace(
        self,
        msg: M,
        text: Optional[Union[str, bytes]] = None,
        attachments: Optional[Iterable[Attachment]] = None
    ) -> M:
        if text is not None:
            msg.text = text
        if attachments is not None:
            msg.attachments = attachments
        return await self.repo.store(msg)

    async def slice(
        self,
        holder: T,
        offset: int = -1, count: int = 100
    ) -> Iterable[Message[T]]:
        return await self.repo.slice(offset=offset, count=count, holder=holder)

    async def delete(self, msg: Message):
        return await self.repo.delete(msg)


class Dialogs(UsecaseSet[Dialog]):

    async def get(self, user: User, colocutor: User) -> Optional[Dialog]:
        return await self.repo.get(user=user, colocutor=colocutor)

    async def list(self, user: User) -> Iterable[Dialog]:
        return await self.repo.search(user=user)


class Conferences(UsecaseSet[Conference]):

    async def get(self, id: int) -> Optional[Conference]:
        return await self.repo.get(id=id)

    async def list(self, user: User) -> Iterable[Dialog]:
        return await self.repo.search(user=user)
