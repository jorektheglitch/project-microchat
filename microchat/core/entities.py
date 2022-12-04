from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime as dt
from enum import Enum, auto
from hashlib import sha3_512

from pathlib import Path

from types import TracebackType
from typing import Literal
from typing import Generic, TypeVar

from .types import Bound, BoundSequence
from .types import MIMEType, MIMESubtype, MIMETuple
from .types import AudiosMIME, ImagesMIME, VideosMIME


C = TypeVar('C', "Conference", "Dialog")  # C means Conversation
T = TypeVar('T')
E = TypeVar('E', bound=Exception)


class Entity(ABC):
    pass


class Named(ABC):
    id: int
    alias: str
    title: str
    avatar: Image
    avatars: BoundSequence[Image]
    default_permissions: Permissions


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


Actor = TypeVar("Actor", bound=User | Bot)


class Relation(Entity, ABC, Generic[Actor]):
    actor: Actor
    related: User | Bot | Conference
    permissions: Permissions | None


class BotRelation(Relation[Bot], ABC):
    related: User | Conference


class Dialog(Relation[User]):
    related: User | Bot
    messages: BoundSequence[Message]


class ConferencePresence:
    join_at: int  # join message id
    leave_at: int | None  # leave message id


class ConferenceParticipation(Relation[Actor], Generic[Actor]):
    no: int  # index of participant
    related: Conference
    role: str
    presences: BoundSequence[ConferencePresence]


class Conference(Entity, Named, Owned[User]):
    description: str | None
    private: bool
    members: BoundSequence[ConferenceParticipation[User | Bot]]
    users: BoundSequence[ConferenceParticipation[User]]
    bots: BoundSequence[ConferenceParticipation[Bot]]
    default_permissions: Permissions
    messages: BoundSequence[Message]


class AuthMethod(Enum):
    PASSWORD = auto()
    PUBLIC_KEY = auto()


class Authentication:
    method: AuthMethod
    user: User
    data: bytes

    def check(self, data: bytes) -> bool:
        if self.method is AuthMethod.PASSWORD:
            return self.data == sha3_512(data)
        method = self.method.name
        raise NotImplementedError(
            f"'{method}' authentication method is not implemented yet"
        )


class Session(Entity):
    id: int
    name: str
    last_active: dt
    location: tuple[str, str, str] | None  # continent, country, city
    ip_address: str
    auth: Authentication
    closed: bool


class Media(Entity, ABC):
    file_info: FileInfo
    name: str  # displayed file name
    type: MIMEType  # MIME type
    subtype: MIMESubtype  # MIME subtype
    loaded_at: dt
    loaded_by: User | Bot


M = TypeVar("M", bound=Media)


class Image(Media):
    type: Literal[MIMEType.IMAGE]
    subtype: ImagesMIME
    preview: Preview


class Video(Media):
    type: Literal[MIMEType.VIDEO]
    subtype: VideosMIME
    preview: Preview


class Audio(Media):
    type: Literal[MIMEType.AUDIO]
    subtype: AudiosMIME


class Animation(Media):
    type: Literal[MIMEType.VIDEO]
    subtype: Literal[VideosMIME.WEBM]
    preview: Preview


class File(Media):
    pass


class Preview(Media):
    file_info: FileInfo
    type: Literal[MIMEType.IMAGE]
    subtype: Literal[ImagesMIME.JPEG]


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


class Message(Entity):  # , Generic[C]):
    id: int  # internal (DB) id
    no: int  # number of message in dialog/conference  # it is just index
    sender: Bound[User | Bot]
    text: str | None
    attachments: BoundSequence[Attachment[Media]]
    time_sent: dt
    time_edit: dt | None
    reply_to: Message | None


class Attachment(Generic[M]):
    no: int  # index of attachment in all of attachments in dialog
    media: M


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

MIME_TUPLES: dict[tuple[str, str], MIMETuple] = {
    **{("image", item.value): (MIMEType.IMAGE, item) for item in ImagesMIME},
    **{("audio", item.value): (MIMEType.AUDIO, item) for item in AudiosMIME},
    **{("video", item.value): (MIMEType.VIDEO, item) for item in VideosMIME},
}
