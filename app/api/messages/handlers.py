from aiohttp import web

from app.utils import is_empty
from app.core.auth import auth_required
from app.core.messages import store_pm, get_pms, overview_pms


@auth_required
async def send_message(request: web.Request):
    data = await request.post()
    from_id = request['user_id']
    reply_to = data.get('reply_to')
    to_id = int(data.get('to'))
    text = data.get('text')
    raw_attachments = data.get('attachments', '')
    attachments = [int(attach) for attach in raw_attachments.split()]
    chat_type = int(data.get('chat_type', 1))
    reply_to = int(reply_to) if reply_to is not None else reply_to
    if is_empty(text) and not raw_attachments:
        raise ValueError('empty message')
    await store_pm(from_id, to_id, text, attachments, chat_type)
    response = {
        "status": 0
    }
    return web.json_response(response)


@auth_required
async def get_messages(request: web.Request):
    data = await request.json()
    user_id = request['user_id']
    chat_id = data.get('user_id')
    if chat_id is None:
        raise ValueError('missing user_id')
    offset = data.get('offset', 0)
    count = data.get('count', 100)
    chat_type = data.get('chat_type', 1)
    chat_id, offset, count = map(int, (chat_id, offset, count))
    messages = await get_pms(user_id, chat_id, offset, count, chat_type)
    return web.json_response({
        "status": 0,
        "result": messages
    })


@auth_required
async def get_chats(request: web.Request):
    user_id = request['user_id']
    return web.json_response({
        "status": 0,
        "result": await overview_pms(user_id)
    })
