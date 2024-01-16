from typing import Any
from aiohttp import web

from microchat import api
from microchat.api.events import EventsSubscribe
from microchat.app.route import Route, APIRoute, HTTPMethod, InternalHandler

from .misc import get_access_token


async def events_request_params(request: web.Request) -> EventsSubscribe:
    access_token = get_access_token(request)
    return EventsSubscribe(access_token)


routes: list[APIRoute[Any]] = [
    Route("/events", HTTPMethod.GET,
          InternalHandler(api.events.get_event_stream, events_request_params))
]
