from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime as dt
from itertools import chain
from typing import ContextManager, Generic, Literal, Protocol, TypeAlias, TypeVar

from microchat.mime import MIMEType, MIMETuple, GeneralMIMEType, AnimationMIMETuple
from microchat.mime import AudiosMIME, ImagesMIME, VideosMIME
from microchat.hashing import Hash, HashableItem, Reference, References, ExternalReference


Signature: TypeAlias = bytes

Emoji: TypeAlias = str


class PubKey(Protocol):
    @property
    @abstractmethod
    def raw(self) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def verify(self, data: bytes, signature: Signature) -> None:
        raise NotImplementedError


# NOTE: decide on types of identites, e.g. Anonymous, Bridge, Puppet, etc
@dataclass(frozen=True)
class Identity(HashableItem):
    pubkey: PubKey

    @property
    def hash(self) -> Hash:
        return Hash(b"stub")


@dataclass(frozen=True)
class EventBase(HashableItem, ABC):
    actor: Identity
    datetime: dt


@dataclass(frozen=True)
class Flag(HashableItem, ABC):
    actor: Identity


AnyEvent = TypeVar("AnyEvent", bound=EventBase | Flag)


@dataclass(frozen=True)
class OriginationEvent(EventBase, ABC):
    pass


@dataclass(frozen=True)
class Event(EventBase, ABC):
    leaf_events: EventOrdering[ConferenceStart | ConferenceEvent]


@dataclass(frozen=True)
class EventOrdering(References[AnyEvent]):
    others_events: References[AnyEvent]
    own_events: References[AnyEvent]

    def __new__(cls, others_events: References[AnyEvent], own_events: References[AnyEvent]):
        return super().__new__(cls, chain(others_events, own_events))


@dataclass(frozen=True)
class SignedEventContainer(Generic[AnyEvent]):
    event: AnyEvent
    signature: Signature

    def verify(self) -> None:
        self.event.actor.pubkey.verify(self.signature, self.event.hash.raw)


@dataclass(frozen=True)
class ConferenceStart(OriginationEvent):
    title: str
    idempotency_mark: str

    @property
    def creator(self) -> Identity:
        return self.actor

    @property
    def hash(self) -> Hash:
        return Hash(b"stub")


@dataclass(frozen=True)
class Invite(Event):
    conference: Reference[ConferenceStart]
    invitee: Identity

    @property
    def inviter(self) -> Identity:
        return self.actor

    @property
    def hash(self) -> Hash:
        return Hash(b"stub")


@dataclass(frozen=True)
class InviteAccept(Event):
    invite: Reference[Invite]

    @property
    def hash(self) -> Hash:
        return Hash(b"stub")


AnyMessage = TypeVar("AnyMessage", bound='Message')


@dataclass(frozen=True)
class MessageEvent(Event, Generic[AnyMessage]):
    conference_acceptance: Reference[InviteAccept]
    reply_to: Reference[MessageLikeEvent] | None = None
    message: AnyMessage = field(kw_only=True)

    @property
    def sent_at(self) -> dt:
        return self.datetime

    @property
    def hash(self) -> Hash:
        return Hash(b"stub")


@dataclass(frozen=True)
class MessageEditEvent(Event, Generic[AnyMessage]):
    edited: Reference[MessageEvent[AnyMessage] | MessageEditEvent[AnyMessage]]
    edit: AnyMessage

    @property
    def hash(self) -> Hash:
        return Hash(b"stub")


@dataclass(frozen=True)
class MessageDeleteEvent(Event):
    deleted: Reference[MessageEvent[Message]]

    @property
    def hash(self) -> Hash:
        return Hash(b"stub")


@dataclass(frozen=True)
class TextMessage(HashableItem):
    text: str
    attachments: References[Media] | None = None

    @property
    def hash(self) -> Hash:
        return Hash(b"stub")


@dataclass(frozen=True)
class StickerMessage(HashableItem):
    sticker: Sticker

    @property
    def hash(self) -> Hash:
        return Hash(b"stub")


@dataclass(frozen=True)
class VoiceMessage(HashableItem):
    audio: Audio

    @property
    def hash(self) -> Hash:
        return Hash(b"stub")


@dataclass(frozen=True)
class VideoMessage(HashableItem):
    video: Video

    @property
    def hash(self) -> Hash:
        return Hash(b"stub")


@dataclass(frozen=True)
class Forward(HashableItem):
    messages: References[MessageEvent[Message]]


@dataclass(frozen=True)
class Reaction(Event):
    message: MessageEvent[Message]
    emoji: Emoji


Message: TypeAlias = TextMessage | StickerMessage | VoiceMessage | VideoMessage | Forward
EditableMessage: TypeAlias = TextMessage
MessageEdit: TypeAlias = (
    MessageEditEvent[TextMessage]
)
MessageEventType: TypeAlias = (
    MessageEvent[TextMessage] |
    MessageEvent[StickerMessage] |
    MessageEvent[VoiceMessage] |
    MessageEvent[VideoMessage] |
    MessageEvent[Forward]
)
MessageLikeEvent: TypeAlias = MessageEventType | MessageEdit | InviteAccept
ConferenceEvent: TypeAlias = (
    Invite | InviteAccept |
    MessageEventType | MessageEdit | MessageDeleteEvent |
    Reaction
)


@dataclass(frozen=True)
class MediaBase(HashableItem, ABC):
    content: ExternalReference[BLOB]
    name: str  # displayed file name
    type: MIMETuple  # MIME type

    @property
    def hash(self) -> Hash:
        return Hash(b"stub")


@dataclass(frozen=True)
class File(MediaBase):
    type: tuple[GeneralMIMEType | str, str]


@dataclass(frozen=True)
class Audio(MediaBase):
    type: tuple[Literal[MIMEType.AUDIO], AudiosMIME]


@dataclass(frozen=True)
class Image(MediaBase):
    type: tuple[Literal[MIMEType.IMAGE], ImagesMIME]


@dataclass(frozen=True)
class Animation(MediaBase):
    type: AnimationMIMETuple


@dataclass(frozen=True)
class Video(MediaBase):
    type: tuple[Literal[MIMEType.VIDEO], VideosMIME]


Media: TypeAlias = Audio | Image | Animation | Video | File


@dataclass(frozen=True)
class Sticker(HashableItem):
    image: Reference[Image | Animation]
    emoji: Emoji


class Reader(Protocol):
    @abstractmethod
    def read(self, chunk_size: int | None = None) -> bytes:
        raise NotImplementedError


class BLOB(Protocol):
    @abstractmethod
    def open(self) -> ContextManager[Reader]:
        raise NotImplementedError
