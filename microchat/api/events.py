from asyncio import Queue
from dataclasses import dataclass

from microchat.services import ServiceSet
from microchat.core.entities import User
from microchat.core.events import Event

from microchat.api_utils.request import AuthenticatedRequest
from microchat.api_utils.response import APIResponse
from microchat.api_utils.handler import authenticated


@dataclass
class EventsSubscribe(AuthenticatedRequest):
    pass


@authenticated
async def get_event_stream(request: EventsSubscribe, services: ServiceSet, user: User) -> APIResponse[Queue[Event]]:
    events: Queue[Event] = await services.events.get_event_stream(user)
    return APIResponse(events)
