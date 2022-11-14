from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, fields
from datetime import datetime as dt
from enum import Enum, auto

from pathlib import Path
from typing import Any, Literal
from typing import Generic, TypeVar

from .types import BoundSequence
from .types import MIMEType, AudiosMIME, ImagesMIME, VideosMIME


C = TypeVar('C', "Conference", "Dialog")  # C means Conversation
T = TypeVar('T')


class Entity(ABC):
    pass


class Named(ABC):
    id: int
    username: str
    title: str
    avatar: Image


class Owned(ABC, Generic[T]):
    owner: T


class Privileges(Enum):
    MODERATOR = auto()
    ADMIN = auto()


class User(Entity, Named):
    privileges: Privileges | None
    name: str
    surname: str | None
    bio: str | None
    dialogs: BoundSequence[Dialog]
    conferences: BoundSequence[Conference]
    sessions: BoundSequence[Session]


class Bot(Entity, Named, Owned[User]):
    description: str | None
    dialogs: BoundSequence[Dialog]
    conferences: BoundSequence[Conference]


class Dialog(Entity, Owned[User]):
    colocutor: User | Bot
    name: str
    surname: str | None
    permissions: Permissions
    messages: BoundSequence[Message]


class ConferencePresence:
    join_at: int  # join message id
    leave_at: int | None  # leave message id


class ConferenceMember(User):
    role: str
    permissions: Permissions | None
    restrictions: Restrictions | None
    presences: BoundSequence[ConferencePresence]


class ConferenceBot(Bot):
    role: str
    permissions: Permissions | None
    restrictions: BoundSequence[Restrictions]
    presences: BoundSequence[ConferencePresence]


class Conference(Entity, Named, Owned[User]):
    description: str | None
    members: BoundSequence[ConferenceMember]
    bots: BoundSequence[ConferenceBot]
    default_permissions: Permissions
    messages: BoundSequence[Message]


class Authentication:
    method: str
    user: User
    data: Any  # type: ignore


class Session(Entity):
    name: str
    last_active: dt
    location: tuple[str, str, str] | None  # continent, country, city
    ip_address: str
    token: str
    auth: Authentication


class Message(Entity):  # , Generic[C]):
    id: int  # internal (DB) id
    no: int  # number of message in dialog/conference  # it is just index
    sender: User | Bot
    text: str | None
    attachments: BoundSequence[Media]
    time_sent: dt
    time_edit: dt | None
    reply_to: Message | None


class Media(Entity, ABC):
    file_info: FileInfo
    name: str  # displayed file name
    type: MIMEType  # MIME type
    subtype: str  # MIME subtype
    loaded_at: dt
    loaded_by: User | Bot


class Image(Media):
    type: Literal["image"]
    subtype: ImagesMIME


class Video(Media):
    type: Literal["video"]
    subtype: VideosMIME


class Audio(Media):
    type: Literal["audio"]
    subtype: AudiosMIME


class Animation(Media):
    type: Literal["video"]
    subtype: Literal["webm"]


class File(Media):
    pass


class FileInfo:
    path: Path
    hash: bytes
    size: int


class Restrictions(Entity):
    since: dt
    to: dt
    restictor: User | Bot
    read: Literal[False] | None = None
    send: Literal[False] | None = None
    delete: Literal[False] | None = None
    send_media: Literal[False] | None = None
    send_mediamessage: Literal[False] | None = None
    add_user: Literal[False] | None = None
    pin_message: Literal[False] | None = None
    edit_conference: Literal[False] | None = None


class Permissions(Entity):
    read: bool
    send: bool
    delete: bool
    send_media: bool
    send_mediamessage: bool
    add_user: bool
    pin_message: bool
    edit_conference: bool


@dataclass
class PermissionsUpdate:
    read: bool | None
    send: bool | None
    delete: bool | None
    send_media: bool | None
    send_mediamessage: bool | None
    add_user: bool | None
    pin_message: bool | None
    edit_conference: bool | None


PERMISSIONS_FIELDS = tuple(field.name for field in fields(PermissionsUpdate))
