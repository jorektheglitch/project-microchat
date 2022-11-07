"""
Модуль содержащий классы, описывающие сущности предметной области (домена).
"""


from __future__ import annotations
from abc import ABC

from datetime import datetime as dt
from pathlib import Path
from typing import Any, Optional, Union
from typing import Generic, TypeVar

from .types import BoundSequence
# from .utils import EntityMeta


C = TypeVar('C', "Conference", "Dialog")  # C means Conversation
T = TypeVar('T')


class Entity(ABC):  # (metaclass=EntityMeta):
    """
    Базовый класс для всех сущностей предметной области.
    """
    # File - файлы в некотором хранилище


class NamedEntity(Entity):

    id: int
    username: str


class User(NamedEntity):

    name: str
    surname: Optional[str]
    bio: Optional[str]
    dialogs: BoundSequence[Dialog]
    conferences: BoundSequence[Conference]


class Bot(NamedEntity):

    title: str
    owner: User
    description: str


class ConferenceMember(User):

    role: str
    permissions: Permissions


class Conference(NamedEntity):

    title: str
    owner: User
    members: BoundSequence[ConferenceMember]
    bots: BoundSequence[Bot]
    default_permissions: Permissions
    messages: BoundSequence[Message[Conference]]


class Dialog(Entity):

    user: User
    colocutor: User
    name: str
    surname: str
    permissions: Permissions
    messages: BoundSequence[Message[Dialog]]


class Authentication(Entity):

    method: str
    user: User
    data: Any


class Session(Entity):

    token: bytes
    auth: Authentication


class Message(Entity, Generic[C]):

    id: int  # internal (DB) id
    no: int  # number of message in dialog/conference  # it is just index
    sender: User
    holder: C
    text: Union[str, bytes]  # for futher functionality (encrypted messages)
    attachments: BoundSequence[Attachment]
    time_sent: dt
    time_edit: Optional[dt]
    reply_to: Optional[Message[C]]


class Attachment(Entity):

    file: File
    name: str  # displayed file name
    type: str  # MIME type
    loaded_at: dt
    loaded_by: User


class File(Entity):

    path: Path
    hash: bytes
    size: int


class Permissions(Entity):

    read: bool
    send: bool
    delete: bool
    send_media: bool
    send_mediamessage: bool
    add_user: bool
    bind_message: bool
    edit_conference: bool
