from aiohttp import web

from microchat.services import ServiceSet
from microchat.core.entities import Image, User

from microchat.api_utils import APIResponse, HTTPStatus, api_handler
from microchat.api_utils import BadRequest, Forbidden, NotFound


router = web.RouteTableDef()


@router.get("/")
@api_handler
async def list_chats(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    offset = payload.get("offset", 0)
    count = payload.get("count", 100)
    if not (isinstance(offset, int) and isinstance(count, int)):
        raise BadRequest("Invalid parameters")
    chats = await services.chats.list_chats(user, offset, count)
    return APIResponse(chats)


@router.get(r"/@{alias:\w+}")
@api_handler
async def get_chat_info(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    alias = request.match_info.get("alias")
    if not alias:
        raise BadRequest("Empty username")
    chat_info = await services.chats.resolve_alias(user, alias)
    return APIResponse(chat_info)


@router.delete(r"/@{alias:\w+}")
@api_handler
async def remove_chat(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    alias = request.match_info.get("alias")
    if not alias:
        raise BadRequest("Empty username")
    chat = await services.chats.resolve_alias(user, alias)
    if chat.owner != user and not user.privileges:
        raise Forbidden("Access denied")
    await services.chats.remove_chat(user, chat)
    return APIResponse(status=HTTPStatus.NO_CONTENT)


@router.get(r"/@{alias:\w+}/avatars")
@api_handler
async def list_chat_avatars(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    alias = request.match_info.get("alias")
    if not alias:
        raise BadRequest("Empty username")
    offset = payload.get("offset", 0)
    count = payload.get("count", 100)
    if not (isinstance(offset, int) and isinstance(count, int)):
        raise BadRequest("Invalid parameters")
    chat = await services.chats.resolve_alias(user, alias)
    avatars = await services.chats.list_chat_avatars(
        user, chat, offset, count
    )
    return APIResponse(avatars)


@router.post(r"/@{alias:\w+}/avatars")
@api_handler
async def set_chat_avatar(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    alias = request.match_info.get("alias")
    if not alias:
        raise BadRequest("Empty username")
    image_id = payload.get("image")
    if not image_id or not isinstance(image_id, int):
        raise BadRequest("Invalid parameters")
    chat = await services.chats.resolve_alias(user, alias)
    if chat.owner != user and not user.privileges:
        raise Forbidden("Access denied")
    avatar = await services.files.get_info(user, image_id)
    if not isinstance(avatar, Image):
        raise BadRequest("Given id does not refers to image")
    await services.chats.set_chat_avatar(user, chat, avatar)
    chat = await services.chats.resolve_alias(user, alias)
    return APIResponse(avatar)


@router.delete(r"/@{alias:\w+}/avatars/{id:\d+}")
@api_handler
async def remove_chat_avatar(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    alias = request.match_info.get("alias")
    id = request.match_info.get("id", -1)
    if not (alias and isinstance(id, int)):
        raise BadRequest("Empty username or avatar id")
    chat = await services.chats.resolve_alias(user, alias)
    if chat.owner != user and not user.privileges:
        raise Forbidden("Access denied")
    await services.chats.remove_chat_avatar(user, chat, id)
    return APIResponse(status=HTTPStatus.NO_CONTENT)


@router.get(r"/@{alias:\w+}/messages")
@api_handler
async def list_chat_messages(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    alias = request.match_info.get("alias")
    if not alias:
        raise BadRequest("Empty username")
    offset = payload.get("offset", 0)
    count = payload.get("count", 100)
    if not (isinstance(offset, int) and isinstance(count, int)):
        raise BadRequest("Invalid parameters")
    chat = await services.chats.resolve_alias(user, alias)
    messages = await services.chats.list_chat_messages(
        user, chat, offset, count
    )
    return APIResponse(messages)


@router.post(r"/@{alias:\w+}/messages")
@api_handler
async def send_message(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    alias = request.match_info.get("alias")
    if not alias:
        raise BadRequest("Empty username")
    text = payload.get("text")
    attachments_ids = payload.get("attachments", [])
    reply_to_id = payload.get("reply_to")
    if not (text is None or isinstance(text, str)):
        raise BadRequest("Message text must be a string")
    if not isinstance(attachments_ids, list):
        raise BadRequest("Attachments IDs must be list of integers")
    if not all(isinstance(item, int) for item in attachments_ids):
        raise BadRequest("Attachments IDs must be list of integers")
    chat = await services.chats.resolve_alias(user, alias)
    reply_to = None
    if reply_to_id:
        reply_to = await services.chats.get_chat_message(
            user, chat, reply_to_id
        )
    attachments = await services.files.get_infos(user, attachments_ids)
    message = await services.chats.add_chat_message(
        user, chat, text, attachments, reply_to
    )
    return APIResponse(message)


@router.get(r"/@{alias:\w+}/messages/{id:\d+}")
@api_handler
async def get_chat_message(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    pass


@router.patch(r"/@{alias:\w+}/messages/{id:\d+}")
@api_handler
async def edit_chat_message(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    pass


@router.delete(r"/@{alias:\w+}/messages/{id:\d+}")
@api_handler
async def remove_chat_message(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    pass


@router.get(r"/@{alias:\w+}/messages/{media_type:(photo|video|audio|animation|file)s}")  # noqa
@api_handler
async def list_chat_media(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    pass


@router.get(r"/@{alias:\w+}/messages/{media_type:(photo|video|audio|animation|file)s}/{id:\d+}")  # noqa
@api_handler
async def get_chat_media(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    pass
