from aiohttp import web

from microchat.core.entities import User, Media
from microchat.core.entities import Animation, Audio, File, Image, Video
from microchat.services import ServiceSet

from microchat.api_utils.response import APIResponse, Status
from microchat.api_utils.exceptions import BadRequest, NotFound
from microchat.api_utils.handler import api_handler
from microchat.api_utils.handler import with_services, wrap_api_response

from .misc import authenticate_media_request
from .misc import get_offset_count
from .misc import get_chat, get_chat_message_attachment_content


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
    relation = await get_chat(services, user, request.match_info)
    return APIResponse(relation)


@router.get(r"/{entity_id:\d+}/messages")
@router.get(r"/@{alias:\w+}/messages")
@api_handler
async def list_chat_messages(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    offset, count = get_offset_count(request)
    chat = await get_chat(services, user, request.match_info)
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
    text = payload.get("text")
    attachments_ids = payload.get("attachments", [])
    reply_to_id = payload.get("reply_to")
    if not (text is None or isinstance(text, str)):
        raise BadRequest("Message text must be a string")
    if not isinstance(attachments_ids, list):
        raise BadRequest("Attachments IDs must be list of integers")
    if not all(isinstance(item, int) for item in attachments_ids):
        raise BadRequest("Attachments IDs must be list of integers")
    chat = await get_chat(services, user, request.match_info)
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
    id = request.match_info["id"]
    message_id = int(id)
    chat = await get_chat(services, user, request.match_info)
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
    id = request.match_info["id"]
    message_id = int(id)
    text = payload.get("text")
    if not (isinstance(text, str) or text is None):
        raise BadRequest("Text must be string")
    attachments_ids = payload.get("attachments")
    chat = await get_chat(services, user, request.match_info)
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
    id = request.match_info["id"]
    message_id = int(id)
    chat = await get_chat(services, user, request.match_info)
    await services.chats.remove_chat_message(user, chat, message_id)
    return APIResponse(status=Status.NO_CONTENT)


@router.get(r"/{entity_id:\d+}/messages/{message_id:\d+}/attachments/{id:\w+}/{view:(preview|content)}")
@router.get(r"/@{alias:\w+}/messages/{message_id:\d+}/attachments/{id:\w+}/{view:(preview|content)}")
@wrap_api_response
@with_services
async def get_attachment_content(
    request: web.Request, services: ServiceSet
) -> APIResponse:
    user = await authenticate_media_request(request, services)
    payload, headers = await get_chat_message_attachment_content(
        services, user, request.match_info
    )
    return APIResponse(payload, headers=headers)


MEDIA_TYPE = r"{media_type:(photo|video|audio|animation|file)s}"


@router.get(r"/{entity_id:\d+}/messages/" + MEDIA_TYPE)
@router.get(r"/@{alias:\w+}/messages/" + MEDIA_TYPE)
@api_handler
async def list_chat_media(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    media_type = request.match_info.get("media_type", '')
    MediaType = MEDIA_CLASSES.get(media_type)
    if MediaType is None:
        raise NotFound(f"Unknown media type: '{media_type}'")
    offset, count = get_offset_count(request)
    chat = await get_chat(services, user, request.match_info)
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
    id = request.match_info.get("id", "-1")
    message_id = int(id)
    media_type = request.match_info.get("media_type", '')
    MediaType = MEDIA_CLASSES.get(media_type)
    if MediaType is None:
        raise NotFound(f"Unknown media type: '{media_type}'")
    chat = await get_chat(services, user, request.match_info)
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
    id = request.match_info.get("id", "-1")
    message_id = int(id)
    media_type = request.match_info.get("media_type", '')
    MediaType = MEDIA_CLASSES.get(media_type)
    if MediaType is None:
        raise NotFound(f"Unknown media type: '{media_type}'")
    chat = await get_chat(services, user, request.match_info)
    await services.chats.remove_chat_media(
        user, chat, MediaType, message_id
    )
    return APIResponse(status=Status.NO_CONTENT)
