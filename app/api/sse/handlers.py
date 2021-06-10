import asyncio

from aiohttp import web
from aiohttp_sse import sse_response

from app.core.sse import ServerSentEventsAPI
from app.core.auth import sse_auth_required


sse_api = ServerSentEventsAPI()


@sse_auth_required
async def all_events(request: web.Request):
    user_id: int = request["user_id"]
    events_queue: asyncio.Queue = sse_api.get_events_queue(user_id)
    async with sse_response(request) as resp:
        while True:
            try:
                event = await events_queue.get()  # CancelledError
            except asyncio.CancelledError:
                break
            else:
                body = event.as_json()
                e_type = event.__class__.__name__
                await resp.send(body, event=e_type)
    await sse_api.del_events_queue(user_id, events_queue)
    return resp
