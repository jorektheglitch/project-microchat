import json

from aiohttp import web

from app.utils import is_empty
from app.core.auth import auth_required
from app.core.messages import store_pm, get_pms, overview_pms


@auth_required
async def send_message(request: web.Request):
    data = await request.post()
    from_id = request['user_id']
    to_id = data.get('to', '')
    text = data.get('text', '')
    raw_attachments = data.get('attachments', '')
    chat_type = data.get('chat_type', 1)
    reply_to = data.get('reply_to')
    if is_empty(text) and not raw_attachments:
        raise web.HTTPBadRequest(
            body=json.dumps({
                "status": 1,
                "error": "empty message"
            }).encode()
        )
    try:
        to_id, chat_type = map(int, (to_id, chat_type))
        attachments = [int(attach) for attach in raw_attachments.split()]
    except (ValueError, TypeError):
        response = {
            "status": 1,
            "error": "incorrect to_id or attachments"
        }
    else:
        try:
            await store_pm(from_id, to_id, text, attachments, chat_type)
            response = {
                "status": 0
            }
        except Exception as e:
            raise web.HTTPInternalServerError(
                reason=e.__class__.__name__,
                body=str(e).encode()
            )
    return web.json_response(response)


@auth_required
async def get_messages(request: web.Request):
    data = await request.json()
    user_id = request['user_id']
    chat_id = data.get('user_id')
    if chat_id is None:
        return web.json_response({
            "status": 1,
            "error": "missing user_id",
        })
    offset = data.get('offset', 0)
    count = data.get('count', 100)
    chat_type = data.get('chat_type', 1)
    try:
        chat_id, offset, count = map(int, (chat_id, offset, count))
        messages = await get_pms(user_id, chat_id, offset, count, chat_type)
    except (TypeError, ValueError) as e:  # noqa
        status = 422
        response = {
            "status": 1,
            "error": "incorrect arguments"
        }
    else:
        status = 200
        response = {
            "status": 0,
            "result": messages
        }
    return web.json_response(response, status=status)


@auth_required
async def get_chats(request: web.Request):
    user_id = request['user_id']
    return web.json_response({
        "status": 0,
        "result": await overview_pms(user_id)
    })
