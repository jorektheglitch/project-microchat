from aiohttp import web

from microchat.services import ServiceSet
from microchat.core.entities import User, Media
from microchat.core.entities import Animation, Audio, File, Image, Video

from microchat.api_utils import APIResponse, HTTPStatus
from microchat.api_utils import api_handler, with_services
from microchat.api_utils import BadRequest, NotFound

from .misc import get_chat, get_offset_count


router = web.RouteTableDef()


MEDIA_CLASSES: dict[str, type[Media]] = {
    "photo": Image,
    "video": Video,
    "audio": Audio,
    "animation": Animation,
    "file": File
}


@router.get("/")
@api_handler
async def list_chats(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    offset, count = get_offset_count(request)
    chats = await services.chats.list_chats(user, offset, count)
    return APIResponse(chats)


@router.get(r"/{entity_id:\d+}")
@router.get(r"/@{alias:\w+}")
@api_handler
async def get_chat_info(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    relation = await get_chat(services, user, entity_id, alias)
    return APIResponse(relation)


@router.get(r"/{entity_id:\d+}/messages")
@router.get(r"/@{alias:\w+}/messages")
@api_handler
async def list_chat_messages(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    offset, count = get_offset_count(request)
    chat = await get_chat(services, user, entity_id, alias)
    messages = await services.chats.list_chat_messages(
        user, chat, offset, count
    )
    return APIResponse(messages)


@router.post(r"/{entity_id:\d+}/messages")
@router.post(r"/@{alias:\w+}/messages")
@api_handler
async def send_message(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    text = payload.get("text")
    attachments_ids = payload.get("attachments", [])
    reply_to_id = payload.get("reply_to")
    if not (text is None or isinstance(text, str)):
        raise BadRequest("Message text must be a string")
    if not isinstance(attachments_ids, list):
        raise BadRequest("Attachments IDs must be list of integers")
    if not all(isinstance(item, int) for item in attachments_ids):
        raise BadRequest("Attachments IDs must be list of integers")
    chat = await get_chat(services, user, entity_id, alias)
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


@router.get(r"/{entity_id:\d+}/messages/{id:\d+}")
@router.get(r"/@{alias:\w+}/messages/{id:\d+}")
@api_handler
async def get_chat_message(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    id = request.match_info["id"]
    message_id = int(id)
    chat = await get_chat(services, user, entity_id, alias)
    message = await services.chats.get_chat_message(user, chat, message_id)
    return APIResponse(message)


@router.patch(r"/{entity_id:\d+}/messages/{id:\d+}")
@router.patch(r"/@{alias:\w+}/messages/{id:\d+}")
@api_handler
async def edit_chat_message(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    id = request.match_info["id"]
    message_id = int(id)
    text = payload.get("text")
    if not (isinstance(text, str) or text is None):
        raise BadRequest("Text must be string")
    attachments_ids = payload.get("attachments")
    chat = await get_chat(services, user, entity_id, alias)
    message = await services.chats.get_chat_message(user, chat, message_id)
    if text is None:
        text = message.text
    if attachments_ids is None:
        attachments = list(await message.attachments)
    else:
        if not isinstance(attachments_ids, list):
            raise BadRequest("Attachments IDs must be list of integers")
        attachments = await services.files.get_infos(user, attachments_ids)
    edited_message = await services.chats.edit_chat_message(
        user, chat, message_id, text, attachments
    )
    return APIResponse(edited_message)


@router.delete(r"/{entity_id:\d+}/messages/{id:\d+}")
@router.delete(r"/@{alias:\w+}/messages/{id:\d+}")
@api_handler
async def remove_chat_message(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    id = request.match_info["id"]
    message_id = int(id)
    chat = await get_chat(services, user, entity_id, alias)
    await services.chats.remove_chat_message(user, chat, message_id)
    return APIResponse(status=HTTPStatus.NO_CONTENT)


@router.get(r"/{entity_id:\d+}/messages/{message_id:\d+}/attachments/{id:\w+}/{view:(preview|content)}")
@router.get(r"/@{alias:\w+}/messages/{message_id:\d+}/attachments/{id:\w+}/{view:(preview|content)}")
@with_services
async def get_attachment(
    request: web.Request, services: ServiceSet
) -> web.StreamResponse:
    try:
        auth_cookie = request.cookies["MEDIA_ACCESS"]
        csrf_token = request.query["csrf_token"]
    except KeyError:
        raise web.HTTPForbidden()
    session = await services.auth.resolve_media_token(auth_cookie)
    if session.closed:
        raise web.HTTPForbidden()
    user = session.auth.user
    if not await services.auth.check_csrf_token(user, csrf_token):
        raise web.HTTPForbidden()
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    try:
        chat = await get_chat(services, user, entity_id, alias)
    except BadRequest:
        raise web.HTTPBadRequest()
    message_id = int(request.match_info["message_id"])
    message = await services.chats.get_chat_message(user, chat, message_id)
    attachment_id = int(request.match_info["id"])
    attachment = await message.attachments[attachment_id]
    response = web.StreamResponse()
    view_kind = request.match_info["view"]
    if view_kind == "content":
        media = attachment
        disposition = f"attachment; filename={media.name}"
    else:
        if not isinstance(attachment, (Image, Video, Animation)):
            # preview only for Image, Video or Animation
            raise web.HTTPBadRequest()
        media = attachment.preview
        disposition = "inline"
    response.headers["Content-Disposition"] = disposition
    response.headers["Content-Type"] = f"{media.type}/{media.subtype}"
    chunks = services.files.iter_content(user, media.file_info)
    async for chunk in chunks:
        await response.write(chunk)
    return response


MEDIA_TYPE = r"{media_type:(photo|video|audio|animation|file)s}"


@router.get(r"/{entity_id:\d+}/messages/" + MEDIA_TYPE)
@router.get(r"/@{alias:\w+}/messages/" + MEDIA_TYPE)
@api_handler
async def list_chat_media(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    media_type = request.match_info.get("media_type", '')
    MediaType = MEDIA_CLASSES.get(media_type)
    if MediaType is None:
        raise NotFound(f"Unknown media type: '{media_type}'")
    offset, count = get_offset_count(request)
    chat = await get_chat(services, user, entity_id, alias)
    medias = await services.chats.list_chat_media(
        user, chat, MediaType, offset, count
    )
    return APIResponse(medias)


@router.get(r"/{entity_id:\d+}/messages/" + MEDIA_TYPE + r"/{id:\d+}")
@router.get(r"/@{alias:\w+}/messages/" + MEDIA_TYPE + r"/{id:\d+}")
@api_handler
async def get_chat_media(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    id = request.match_info.get("id", "-1")
    message_id = int(id)
    media_type = request.match_info.get("media_type", '')
    MediaType = MEDIA_CLASSES.get(media_type)
    if MediaType is None:
        raise NotFound(f"Unknown media type: '{media_type}'")
    chat = await get_chat(services, user, entity_id, alias)
    message = await services.chats.get_chat_media(
        user, chat, MediaType, message_id
    )
    return APIResponse(message)


@router.delete(r"/{entity_id:\d+}/messages/" + MEDIA_TYPE + r"/{id:\d+}")
@router.delete(r"/@{alias:\w+}/messages/" + MEDIA_TYPE + r"/{id:\d+}")
@api_handler
async def remove_chat_media(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    id = request.match_info.get("id", "-1")
    message_id = int(id)
    media_type = request.match_info.get("media_type", '')
    MediaType = MEDIA_CLASSES.get(media_type)
    if MediaType is None:
        raise NotFound(f"Unknown media type: '{media_type}'")
    chat = await get_chat(services, user, entity_id, alias)
    await services.chats.remove_chat_media(
        user, chat, MediaType, message_id
    )
    return APIResponse(status=HTTPStatus.NO_CONTENT)
