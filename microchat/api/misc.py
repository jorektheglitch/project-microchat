from typing import AsyncIterable, Literal, Mapping

from aiohttp import web

from microchat.api.params import check_view_kind

from microchat.core.entities import Message, User, Bot, Conference
from microchat.core.entities import Media, Animation, Image, Video
from microchat.core.entities import ConferenceParticipation, Dialog
from microchat.services import ServiceSet, AuthenticationError
from microchat.api_utils.response import HEADER
from microchat.api_utils.exceptions import BadRequest, NotFound


async def authenticate_media_request(
    request: web.Request, services: ServiceSet
) -> User:
    try:
        auth_cookie = request.cookies["MEDIA_ACCESS"]
        csrf_token = request.query["csrf_token"]
    except KeyError:
        raise AuthenticationError
    session = await services.auth.resolve_media_token(
        auth_cookie, csrf_token
    )
    user = session.auth.user
    return user


def get_offset_count(
    request: web.Request, defaults: tuple[int, int] = (0, 100)
) -> tuple[int, int]:
    default_offset, default_count = defaults
    offset = request.query.get("offset", default_offset)
    count = request.query.get("count", default_count)
    try:
        offset = int(offset)
        count = int(count)
    except (ValueError, TypeError):
        raise BadRequest("Invalid 'offset' or 'count' params")
    return offset, count


async def get_entity(
    services: ServiceSet,
    user: User,
    entity_id: str | int | None,
    alias: str | None
) -> User | Bot | Conference:
    if isinstance(entity_id, str):
        entity_id = int(entity_id)
        entity = await services.agents.get(user, entity_id)
    elif alias:
        entity = await services.agents.resolve_alias(user, alias)
    else:
        raise BadRequest
    return entity


async def get_conference(
    services: ServiceSet,
    user: User,
    entity_id: str | int | None,
    alias: str | None
) -> Conference:
    entity = await get_entity(services, user, entity_id, alias)
    if not isinstance(entity, Conference):
        raise NotFound
    return entity


async def get_chat(
    services: ServiceSet,
    user: User,
    match_info: Mapping[str, str]
) -> Dialog | ConferenceParticipation[User]:
    entity_id_repr = match_info.get("entity_id")
    alias = match_info.get("alias")
    if entity_id_repr:
        entity_id = int(entity_id_repr)
        chat = await services.agents.get_chat(user, entity_id)
    elif alias:
        chat = await services.agents.resolve_chat_alias(user, alias)
    else:
        raise BadRequest
    return chat


async def get_chat_message(
    services: ServiceSet,
    user: User,
    match_info: Mapping[str, str]
) -> Message:
    chat = await get_chat(services, user, match_info)
    try:
        message_id_repr = match_info["message_id"]
        message_id = int(message_id_repr)
    except (KeyError, ValueError, TypeError):
        raise BadRequest
    message = await services.chats.get_chat_message(user, chat, message_id)
    return message


async def get_chat_message_attachment(
    services: ServiceSet,
    user: User,
    match_info: Mapping[str, str]
) -> Media:
    message = await get_chat_message(services, user, match_info)
    try:
        attachment_id_repr = match_info["attachment_id"]
        attachment_id = int(attachment_id_repr)
    except (KeyError, ValueError, TypeError):
        raise BadRequest
    attachment = await message.attachments[attachment_id]
    return attachment


async def get_chat_message_attachment_content(
    services: ServiceSet,
    user: User,
    match_info: Mapping[str, str]
) -> tuple[AsyncIterable[bytes], dict[HEADER, str]]:
    attachment = await get_chat_message_attachment(services, user, match_info)
    view_kind = match_info.get("view_kind")
    if not (view_kind and check_view_kind(view_kind)):
        raise BadRequest
    payload, headers = await file_response(
        services, user, attachment, view_kind
    )
    return payload, headers


async def file_response(
    services: ServiceSet,
    user: User,
    attachment: Media,
    view_kind: Literal["content", "preview"]
) -> tuple[AsyncIterable[bytes], dict[HEADER, str]]:
    if view_kind == "content":
        media = attachment
        disposition = f"attachment; filename={media.name}"
    else:
        if not isinstance(attachment, (Image, Video, Animation)):
            media_type = type(attachment).__name__
            raise NotFound(f"Preview for '{media_type}' is unavailable")
        media = attachment.preview
        disposition = "inline"
    payload = services.files.iter_content(user, media.file_info)
    headers = {
        HEADER.ContentDisposition: disposition,
        HEADER.ContentType: f"{media.type}/{media.subtype}"
    }
    return payload, headers
