from __future__ import annotations
from abc import ABC
from datetime import datetime as dt
from enum import Enum, auto

from pathlib import Path
from typing import Any, Literal, Optional
from typing import Generic, TypeVar

from .types import BoundSequence, ImagesMIME, MIMEType


C = TypeVar('C', "Conference", "Dialog")  # C means Conversation
T = TypeVar('T')


class Named(ABC):
    id: int
    username: str
    title: str


class Owned(ABC, Generic[T]):
    owner: T


class Privileges(Enum):
    MODERATOR = auto()
    ADMIN = auto()


class User(Named):
    privileges: Optional[Privileges]
    name: str
    surname: Optional[str]
    bio: Optional[str]
    dialogs: BoundSequence[Dialog]
    conferences: BoundSequence[Conference]
    sessions: BoundSequence[Session]


class Bot(Named, Owned[User]):
    description: Optional[str]
    dialogs: BoundSequence[Dialog]
    conferences: BoundSequence[Conference]


class Dialog(Owned[User]):
    colocutor: User | Bot
    name: str
    surname: Optional[str]
    permissions: Permissions
    messages: BoundSequence[Message]


class ConferencePresence:
    join_at: int  # join message id
    leave_at: int | None  # leave message id


class ConferenceMember(User):
    role: str
    permissions: Permissions
    presences: BoundSequence[ConferencePresence]


class Conference(Named, Owned[User]):
    description: Optional[str]
    members: BoundSequence[ConferenceMember]
    bots: BoundSequence[Bot]
    default_permissions: Permissions
    messages: BoundSequence[Message]


class Authentication:
    method: str
    user: User
    data: Any  # type: ignore


class Session:
    name: str
    last_active: dt
    location: tuple[str, str, str] | None  # continent, country, city
    ip_address: str
    token: str
    auth: Authentication


class Message:  # , Generic[C]):
    id: int  # internal (DB) id
    no: int  # number of message in dialog/conference  # it is just index
    sender: User
    text: str  # for futher functionality (encrypted messages)
    attachments: BoundSequence[Media]
    time_sent: dt
    time_edit: Optional[dt]
    reply_to: Optional[Message]


class Media:
    file: File
    name: str  # displayed file name
    type: MIMEType  # MIME type
    subtype: str  # MIME subtype
    loaded_at: dt
    loaded_by: User


class Image(Media):
    type: Literal["image"]
    subtype: ImagesMIME


class File:
    path: Path
    hash: bytes
    size: int


class Permissions:
    read: bool
    send: bool
    delete: bool
    send_media: bool
    send_mediamessage: bool
    add_user: bool
    bind_message: bool
    edit_conference: bool
