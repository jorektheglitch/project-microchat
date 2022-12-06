from __future__ import annotations

from asyncio import Queue
from dataclasses import dataclass
import enum
import json
import functools

from typing import Any, AsyncIterable, Generic, Sequence, TypeVar

from microchat.core.entities import Entity
from microchat.core.events import Event
from microchat.core.types import JSON


APIResponseBody = Entity | Sequence[Entity] | dict[str, Entity]
# Sequence used instead of list because list is invariant (and then it is
# list[EntityChildClass] is not matched by theese union)

P = TypeVar("P", bound=APIResponseBody | JSON | AsyncIterable[bytes] | Queue[Event], contravariant=True)


class Status(enum.Enum):
    OK = 200
    CREATED = 201
    NO_CONTENT = 204


class HEADER(enum.Enum):
    ContentDisposition = "Content-Disposition"
    ContentType = "Content-Type"


@dataclass
class APIResponse(Generic[P]):
    payload: P
    status: Status = Status.OK
    reason: str | None = None
    headers: dict[str, str] | None = None

    def __init__(
        self,
        payload: P | None = None,
        status: Status = Status.OK,
        reason: str | None = None,
        headers: dict[HEADER, str] | None = None,
    ) -> None:
        if payload is not None:
            self.payload = payload
        self.status = status
        self.reason = reason
        self.headers = {
            key.value: value for key, value in headers.items()
        } if headers else None

    @property
    def status_code(self) -> int:
        return self.status.value


class APIResponseEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:  # type: ignore  # Any not allowed
        if isinstance(o, Entity):
            # TODO: make serialization for all entity types
            pass
        return super().default(o)


DEFAULT_JSON_DUMPER = functools.partial(json.dumps, cls=APIResponseEncoder)
