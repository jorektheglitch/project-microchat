from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping, Set
from itertools import chain
from typing import Literal, Protocol, TypeVar

from microchat.hashing import Hash, Reference, ExternalReference
from microchat.entities import ConferenceStart, ConferenceEvent, Identity, Invite, InviteAccept, BLOB


AnyEvent = TypeVar("AnyEvent", bound=ConferenceStart | ConferenceEvent)


class Storage(Protocol):
    @abstractmethod
    def resolve(
        self,
        reference: Reference[AnyEvent],
        type: type[AnyEvent],
        *,
        match_type: Literal['skip', 'strict']
    ) -> AnyEvent:
        raise NotImplementedError

    @abstractmethod
    def get(self, hash: Hash, type: type[AnyEvent]) -> AnyEvent:
        raise NotImplementedError

    @abstractmethod
    def successors_of(self, *events: AnyEvent) -> Mapping[AnyEvent, Set[ConferenceEvent]]:
        raise NotImplementedError


class MediaStorage(Protocol):
    @abstractmethod
    def get(self, reference: ExternalReference[BLOB]) -> BLOB:
        raise NotImplementedError


class Conference:
    start_event: ConferenceStart
    storage: Storage
    media_storage: MediaStorage

    def members(self) -> Set[Identity]:
        start_successors = self.storage.successors_of(self.start_event)
        invites = [
            successor
            for successor in chain.from_iterable(start_successors.values())
            if isinstance(successor, Invite)
        ]
        invites_successors = {
            invite: {event for event in successors if isinstance(event, InviteAccept)}
            for invite, successors in self.storage.successors_of(*invites).items()
        }
        return {invite.invitee for invite, acceptances in invites_successors.items() if acceptances}
