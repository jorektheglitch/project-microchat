from aiohttp import web

from microchat.api.events import EventsSubscribe

from .misc import get_access_token


async def events_request_params(request: web.Request) -> EventsSubscribe:
    access_token = get_access_token(request)
    return EventsSubscribe(access_token)
