from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime as dt
from enum import Enum, auto

from pathlib import Path

from types import TracebackType
from typing import Any, Literal
from typing import Generic, TypeVar

from .types import Bound, BoundSequence
from .types import MIMEType, AudiosMIME, ImagesMIME, VideosMIME


C = TypeVar('C', "Conference", "Dialog")  # C means Conversation
T = TypeVar('T')
E = TypeVar('E', bound=Exception)


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
    id: int
    name: str
    last_active: dt
    location: tuple[str, str, str] | None  # continent, country, city
    ip_address: str
    auth: Authentication
    closed: bool


class Message(Entity):  # , Generic[C]):
    id: int  # internal (DB) id
    no: int  # number of message in dialog/conference  # it is just index
    sender: Bound[User | Bot]
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
    preview: Preview


class Video(Media):
    type: Literal["video"]
    subtype: VideosMIME
    preview: Preview


class Audio(Media):
    type: Literal["audio"]
    subtype: AudiosMIME


class Animation(Media):
    type: Literal["video"]
    subtype: Literal["webm"]
    preview: Preview


class File(Media):
    pass


class Preview:
    file_info: FileInfo
    type: Literal["image"]
    subtype: Literal["jpeg"]


class FileInfo:
    path: Path
    hash: str
    size: int


class TempFile(ABC):
    hash: bytes
    size: int

    async def __aenter__(self: T) -> T:
        return self

    @abstractmethod
    async def __aexit__(
        self,
        exc_cls: type[E] | None,
        exc: E | None,
        tb: TracebackType | None
    ) -> None:
        pass

    @abstractmethod
    async def write(self, data: bytes) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass


class Restrictions(Entity):
    since: dt
    to: dt
    restictor: Bound[User | Bot]
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


PERMISSIONS_FIELDS = tuple(field for field in Permissions.__annotations__)
