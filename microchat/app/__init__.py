"""
Basic attempt to create some useful thing over invented system.
"""

from __future__ import annotations

import secrets
from abc import abstractmethod
from collections.abc import AsyncGenerator, Callable, Iterable, Iterator, Mapping, Sequence, Set
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime as dt
from functools import wraps
from logging import getLogger
from threading import Lock
from typing import Any, Concatenate, Generator, NoReturn, ParamSpec, Protocol, TypeVar, overload


from microchat.entities import Identity, PrivKey, PubKey
from microchat.entities import ConferenceEvent, EventOrdering, SignedEventContainer, AnyConferenceEvent
from microchat.entities import ConferenceStart, Invite, InviteAccept
from microchat.entities import MessageEvent, TextMessage, Message, StickerMessage, VideoMessage, VoiceMessage
from microchat.entities import Audio, Sticker, Video, Media
from microchat.hashing import Hash, HashableItem, Reference, hash_set
from microchat.storage.dag import DAG


AnySeparateMessage = TypeVar("AnySeparateMessage",
                             # TextMessage, StickerMessage, VoiceMessage, VideoMessage
                             bound=TextMessage | StickerMessage | VoiceMessage | VideoMessage
                             )
Params = ParamSpec("Params")

log = getLogger("microchat")


class HasLock(Protocol):
    _lock: Lock


@contextmanager
def acquire(lock: Lock, timeout: float | None = None) -> Generator[None, Any, None]:
    if timeout is None:
        lock.acquire()
    else:
        lock.acquire(timeout=timeout)
    yield
    lock.release()


def with_lock(fn):
    @wraps(fn)
    def wrapped(self: HasLock, *args, **kwargs):
        with acquire(self._lock, timeout=10):
            return fn(self, *args, **kwargs)
    return wrapped


class NotFound(Exception):
    pass


@dataclass(frozen=True)
class Level(HashableItem):
    references: Set[Reference[ConferenceEvent]]

    def __iter__(self) -> Iterator[Reference[ConferenceEvent]]:
        yield from self.references

    @property
    def hash(self) -> Hash:
        return hash_set({reference.key for reference in self.references})


class Storage:
    _dag: DAG[Reference[ConferenceStart | ConferenceEvent]]
    _items: dict[Reference[ConferenceStart | ConferenceEvent], SignedEventContainer[ConferenceStart | ConferenceEvent]]
    _lock: Lock

    def __init__(self):
        self._dag = DAG()
        self._items = {}
        self._lock = Lock()

    def insert(self, container: SignedEventContainer[ConferenceStart | ConferenceEvent]) -> None:
        event = container.event
        log.debug("Insert event %s of type %s", event.hash.raw[:4].hex(), type(event).__name__)
        reference = event.reference()
        if reference in self._dag.links:
            log.debug("Event %s already exists, do nothing", event.hash.raw[:4].hex())
            return None
        links = {
            item: links
            for item, links in self._dag.links.items()
        }
        links[reference] = event.references  # type: ignore
        if reference not in self._items:
            self._items[reference] = container
        self._dag = DAG(links=links)

    def create(
        self,
        type: Callable[Concatenate[Identity, dt, EventOrdering, Params], AnyConferenceEvent],
        actor: Identity,
        *args: Params.args,
        **kwargs: Params.kwargs
    ) -> AnyConferenceEvent:
        log.debug("Create event of type %s", type.__name__)
        datetime = dt.now()
        leaf_events_refs: tuple[Reference, ...] = tuple(Reference(wrapped.hash) for wrapped in self._dag.sources)
        # TODO: find a way to get own leaf events
        ordering: EventOrdering = EventOrdering(others_events=leaf_events_refs, own_events=())
        event = type(actor, datetime, ordering, *args, **kwargs)
        log.debug("Created event %s of type %s", event.hash.raw[:4].hex(), type.__name__)
        return event

    def get_by_hash(self, hash: Hash, type: type[AnyConferenceEvent]) -> AnyConferenceEvent:
        return self.resolve(Reference(key=hash), type=type)

    def resolve(
        self,
        reference: Reference[AnyConferenceEvent],
        type: type[AnyConferenceEvent] | None = None
    ) -> AnyConferenceEvent:
        try:
            container = self._items[reference]
        except KeyError as e:
            raise NotFound() from e
        item = container.event
        if type and not isinstance(item, type):
            raise TypeError(f"Expected {type.__name__}, but got {item.__class__.__name__}")
        return item  # type: ignore

    async def levels(self, start: Reference[ConferenceStart]) -> AsyncGenerator[Level, None]:
        for level_references in self._dag.levels_from(start):
            yield Level(level_references)
        return

    def events_from(self, start: Reference[ConferenceStart]) -> Iterator[ConferenceEvent]:
        for reference in self._dag.topological_order_from(start):
            container = self._items[reference]
            yield container.event


class Connection(Protocol):
    @abstractmethod
    def send(self, event: SignedEventContainer) -> None:
        pass


@dataclass(frozen=True)
class Client:
    storage: Storage
    signing_key: PrivKey
    event_callblack: Callable[[ConferenceEvent], Any] = (lambda event: None)
    _peers: Mapping[Identity, Connection] = field(default_factory=dict)

    @property
    def identity(self) -> Identity:
        return Identity(pubkey=self.signing_key.public_key)

    def create_event(
        self,
        type: Callable[Concatenate[Identity, dt, EventOrdering, Params], AnyConferenceEvent],
        actor: Identity,
        *args: Params.args,
        **kwargs: Params.kwargs
    ) -> SignedEventContainer[AnyConferenceEvent]:
        event = self.storage.create(type, actor, *args, **kwargs)
        signed_event = self.sign_event(event)
        return signed_event

    def dispatch(self, container: SignedEventContainer[AnyConferenceEvent], peers: Iterable[Identity] = ()) -> None:
        try:
            container.verify()
        except Exception:
            return

        self.storage.insert(container)
        try:
            self.event_callblack(container.event)
        except Exception as exc:
            log.warning("Event callback failed", exc_info=exc)

        for peer in peers:
            conn = self._peers[peer]
            conn.send(container)

    def sign_event(self, event: AnyConferenceEvent) -> SignedEventContainer[AnyConferenceEvent]:
        signature = self.signing_key.sign(event.hash.raw)
        return SignedEventContainer(event=event, signature=signature)

    def verify_event(self, event: SignedEventContainer) -> None:
        return event.verify()

    def create_conference(self, title: str) -> Conference:
        idempotency_mark = secrets.token_urlsafe(nbytes=32)
        conference_start = ConferenceStart(
            actor=self.identity,
            datetime=dt.now(),
            title=title,
            idempotency_mark=idempotency_mark
        )
        signed = self.sign_event(conference_start)
        self.dispatch(signed)
        conference = Conference(conference_start.reference(), conference_start, self)
        return conference

    def accept_invite(self, invite: Invite) -> Conference:
        if invite.invitee != self.identity:
            raise ValueError("Can not accept invite: idenity mismatch")
        invite_accept = self.create_event(InviteAccept, actor=self.identity, invite=invite.reference())
        conference = Conference(invite.conference, invite_accept.event.reference(), self)
        return conference

    async def sync(self, peer: PeerConnection) -> None:
        conferences: list[Conference] = []
        peer.state = PeerState.SYNCING
        for conference in conferences:
            # if peer.identity
            async for level in self.storage.levels(conference._start_ref):
                pass


@dataclass(frozen=True)
class Conference:
    _start_ref: Reference[ConferenceStart]
    _acceptance_ref: Reference[InviteAccept] | ConferenceStart
    _client: Client

    @property
    def _self(self) -> Identity:
        return self._client.identity

    def invite(self, invitee: Identity) -> Invite:
        invite = self._client.create_event(Invite, actor=self._self, conference=self._start_ref, invitee=invitee)
        self._client.dispatch(invite, peers=(invitee,))
        return invite.event

    @property
    def events(self) -> Iterator[ConferenceEvent]:
        yield from self._client.storage.events_from(self._start_ref)

    @property
    def members(self) -> set[Identity]:
        members = set()
        for event in self.events:
            if isinstance(event, InviteAccept):
                members.add(event.actor)
        return members

    @overload
    def send_message(self, reply_to: MessageEvent | None = None, *, text: str) -> MessageEvent[TextMessage]: ...
    @overload
    def send_message(self, reply_to: MessageEvent | None = None, *, attachments: Sequence[Media]) -> MessageEvent[TextMessage]: ...  # noqa: E501
    @overload
    def send_message(self, reply_to: MessageEvent | None = None, *, text: str, attachments: Sequence[Media]) -> MessageEvent[TextMessage]: ...  # noqa: E501
    @overload
    def send_message(self, reply_to: MessageEvent | None = None, *, sticker: Sticker) -> MessageEvent[StickerMessage]: ...  # noqa: E501
    @overload
    def send_message(self, reply_to: MessageEvent | None = None, *, voice: Audio) -> MessageEvent[VoiceMessage]: ...
    @overload
    def send_message(self, reply_to: MessageEvent | None = None, *, record: Video) -> MessageEvent[VideoMessage]: ...

    def send_message(
        self,
        reply_to: MessageEvent | None = None,
        text: str | None = None,
        attachments: Sequence[Media] | None = None,
        sticker: Sticker | None = None,
        voice: Audio | None = None,
        record: Video | None = None
    ) -> MessageEvent[TextMessage] | MessageEvent[StickerMessage] | MessageEvent[VoiceMessage] | MessageEvent[VideoMessage]:  # noqa: E501
        args = {
            "text (or attachments)": text or attachments,
            "sticker": sticker,
            "voice": voice,
            "record": record
        }
        args = {description: value for description, value in args.items() if value}
        if not args:
            raise TypeError()
        if len(args) > 1:
            raise TypeError()

        reply_to_ref = reply_to.reference() if reply_to else None

        message: Message
        if text or attachments:
            attachments_refs = tuple(attachment.reference() for attachment in attachments) if attachments else None
            message = TextMessage(text=text, attachments=attachments_refs)
        elif sticker:
            message = StickerMessage(sticker=sticker)
        elif voice:
            message = VoiceMessage(audio=voice)
        elif record:
            message = VideoMessage(video=record)
        else:
            raise RuntimeError

        message_event = self._client.create_event(
            new_message_event,
            actor=self._self,
            conference_acceptance=self._acceptance_ref,
            reply_to=reply_to_ref,
            message=message
        )
        self._client.dispatch(message_event, peers=self.members)

        return message_event.event


class OwnConference(Conference):
    pass


def new_message_event(
    actor: Identity,
    datetime: dt,
    ordering: EventOrdering,
    conference_acceptance: Reference[InviteAccept] | ConferenceStart,
    reply_to: Reference[MessageEvent] | None,
    message: AnySeparateMessage,  # intended to be used in return MessageEvent[AnySeparateMessage], but mypy got questions
) -> MessageEvent[TextMessage] | MessageEvent[StickerMessage] | MessageEvent[VoiceMessage] | MessageEvent[VideoMessage]:
    return MessageEvent(
        actor=actor,
        datetime=datetime,
        leaf_events=ordering,
        conference_acceptance=conference_acceptance,
        reply_to=reply_to,
        message=message
    )


if __name__ == "__main__":
    import asyncio
    from socket import socket
    from enum import StrEnum, auto

    class PeerState(StrEnum):
        CONNECTED = auto()
        SYNCING = auto()
        SYNCED = auto()
        DEAD = auto()

    @dataclass
    class PeerConnection:
        identity: bytes
        reader: asyncio.StreamReader
        writer: asyncio.StreamWriter
        state: PeerState

    class PeerProtocol(asyncio.Protocol):
        pass

    class Networking:
        """
        Peers state tracking <-> Connectivity keeping <-> DAG Syncronization
        """

        client: Client
        loop: asyncio.AbstractEventLoop
        peers: dict
        new_connections: asyncio.Queue[tuple[asyncio.StreamReader, asyncio.StreamWriter]]

        def add_peer(self, address) -> None:
            pass

        async def add_connection(self, sock: socket) -> None:
            reader = asyncio.StreamReader(loop=self.loop)
            protocol = asyncio.StreamReaderProtocol(reader, loop=self.loop)
            transport, _ = await self.loop.create_connection(
                lambda: protocol, sock=sock)
            writer = asyncio.StreamWriter(transport, protocol, reader, self.loop)
            self.new_connections.put_nowait((reader, writer))

        async def new_connections_processing(self) -> NoReturn:
            while True:
                reader, writer = await self.new_connections.get()
                pubkey_raw = await reader.readexactly()
                pubkey = Ed25519PublicKey(ed25519.Ed25519PublicKey.from_public_bytes(pubkey_raw))
                peer = PeerConnection(identity=pubkey, reader=reader, writer=writer, state=PeerState.CONNECTED)
                await self.client.sync(peer)
