from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime as dt
from typing import Generic, Literal, Protocol, TypeAlias, TypeVar

from microchat.mime import MIMEType, MIMETuple, GeneralMIMEType, AnimationMIMETuple
from microchat.mime import AudiosMIME, ImagesMIME, VideosMIME
from microchat.hashing import HashableItem, Reference, References, ExternalReference


PubKey: TypeAlias = str
Signature: TypeAlias = bytes

Emoji: TypeAlias = str


# NOTE: decide on types of identites, e.g. Anonymous, Bridge, Puppet, etc
@dataclass(frozen=True)
class Identity(HashableItem):
    pubkey: PubKey


@dataclass(frozen=True)
class EventBase(HashableItem, ABC):
    actor: Identity
    datetime: dt
    signature: Signature


@dataclass(frozen=True)
class OriginationEvent(EventBase, ABC):
    pass


@dataclass(frozen=True)
class Event(EventBase, ABC):
    leaf_events: References[EventBase]


@dataclass(frozen=True)
class ConferenceStart(OriginationEvent):
    title: str
    idempotency_mark: str

    @property
    def creator(self) -> Identity:
        return self.actor


@dataclass(frozen=True)
class Invite(Event):
    leaf_events: References[ConferenceStart | ConferenceEvent]
    conference: Reference[ConferenceStart]
    invitee: Identity

    @property
    def inviter(self) -> Identity:
        return self.actor


@dataclass(frozen=True)
class InviteAccept(Event):
    leaf_events: References[ConferenceEvent]
    invite: Reference[Invite]


AnyMessage = TypeVar("AnyMessage", bound='Message')


@dataclass(frozen=True)
class MessageEvent(Event, Generic[AnyMessage]):
    conference_acceptance: Reference[InviteAccept]
    last_others_message: Reference[MessageEvent[Message] | InviteAccept]
    last_own_message: Reference[MessageEvent[Message] | InviteAccept]
    reply_to: Reference[MessageEvent[Message] | InviteAccept | None]
    message: AnyMessage

    @property
    def sent_at(self) -> dt:
        return self.datetime


@dataclass(frozen=True)
class MessageEditEvent(Event, Generic[AnyMessage]):
    edited: Reference[MessageEvent[AnyMessage] | MessageEditEvent[AnyMessage]]
    edit: AnyMessage


@dataclass(frozen=True)
class MessageDeleteEvent(Event):
    deleted: Reference[MessageEvent[Message]]


@dataclass(frozen=True)
class TextMessage(HashableItem):
    text: str
    attachments: References[MediaBase] | None = None


@dataclass(frozen=True)
class StickerMessage(HashableItem):
    sticker: Sticker


@dataclass(frozen=True)
class VoiceMessage(HashableItem):
    audio: Audio


@dataclass(frozen=True)
class VideoMessage(HashableItem):
    video: Video


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
ConferenceEvent: TypeAlias = (
    Invite | InviteAccept |
    MessageEvent[Message] | MessageEdit | MessageDeleteEvent |
    Reaction
)


@dataclass(frozen=True)
class MediaBase(HashableItem, ABC):
    content: ExternalReference[BLOB]
    name: str  # displayed file name
    type: MIMETuple  # MIME type


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
    def open(self) -> Reader:
        raise NotImplementedError
