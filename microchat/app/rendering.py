import asyncio

from typing import AsyncIterable, Awaitable, Callable

from aiohttp import web
from aiohttp import typedefs
from aiohttp_sse import sse_response  # type: ignore

from microchat.api_utils.exceptions import APIError
from microchat.api_utils.response import APIResponse, APIResponseBody
from microchat.api_utils.types import JSON
from microchat.core.events import Event


APIResponseContent = APIResponseBody | JSON | AsyncIterable[bytes] | asyncio.Queue[Event]


def renderer(
    dumps: typedefs.JSONEncoder
) -> Callable[[web.Request, APIResponse[APIResponseContent]], Awaitable[web.Response]]:
    async def render(
        request: web.Request,
        api_response: APIResponse[APIResponseContent]
    ) -> web.Response:
        if isinstance(api_response.payload, AsyncIterable):
            response = web.Response(
                status=api_response.status_code,
                reason=api_response.reason,
                headers=api_response.headers
            )
            await response.prepare(request)
            async for chunk in api_response.payload:
                await response.write(chunk)
        elif isinstance(api_response.payload, asyncio.Queue):
            events_response = sse_response(
                request,
                status=api_response.status_code,
                reason=api_response.reason,
                headers=api_response.headers
            )
            events_queue = api_response.payload
            async with events_response as response:
                while True:
                    try:
                        # may be CancelledError if connection was aborted
                        event = await events_queue.get()
                    except asyncio.CancelledError:
                        break
                    body = event.as_json()
                    event_kind = event.__class__.__name__
                    events_response.send(body, event=event_kind)
        else:
            payload: dict[str, JSON | APIResponseBody]
            if isinstance(api_response, APIError):
                payload = {"error": api_response.payload}
            else:
                payload = {"response": api_response.payload}
            response = web.json_response(
                payload,
                status=api_response.status_code,
                reason=api_response.reason,
                dumps=dumps,
                headers=api_response.headers
            )
        return response
    return render
