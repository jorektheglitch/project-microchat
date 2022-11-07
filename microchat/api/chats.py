from aiohttp import web

from microchat.services import ServiceSet
from microchat.core.entities import User

from microchat.api_utils import APIResponse, Forbidden, HTTPStatus, api_handler
from microchat.api_utils import BadRequest, NotFound


router = web.RouteTableDef()


@router.get("/")
@api_handler
async def list_chats(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest(payload={"error": "invalid body"})
    offset = payload.get("offset", 0)
    count = payload.get("count", 100)
    if not (isinstance(offset, int) or isinstance(count, int)):
        raise BadRequest(payload={"error": "invalid parameters"})
    chats = await services.chats.list_chats(user, offset, count)
    return APIResponse({
        "response": chats
    })


@router.get(r"/@{alias:\w+}")
@api_handler
async def get_chat_info(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest(payload={"error": "invalid body"})
    alias = request.match_info.get("alias")
    if not alias:
        raise BadRequest(payload={"error": "empty username"})
    chat_info = await services.chats.resolve_alias(user, alias)
    return APIResponse({
        "response": chat_info
    })


@router.delete(r"/@{alias:\w+}")
@api_handler
async def remove_chat(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    alias = request.match_info.get("alias")
    chat = await services.chats.resolve_alias(user, alias)
    if chat.owner != user and not user.privileges:
        raise Forbidden(payload={"error": "Access denied"})
    await services.chats.remove_chat(user, chat)
    return APIResponse({}, HTTPStatus.NO_CONTENT)


@router.get(r"/@{alias:\w+}/avatars")
@api_handler
async def list_chat_avatars(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    pass


@router.post(r"/@{alias:\w+}/avatars")
@api_handler
async def set_chat_avatar(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    pass


@router.delete(r"/@{alias:\w+}/avatars/{id:\d+}")
@api_handler
async def revome_chat_avatar(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    pass
