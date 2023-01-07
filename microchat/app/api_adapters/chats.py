from aiohttp import web

from microchat.api.chats import GetMessage, GetChat, GetChatMedia
from microchat.api.chats import GetAttachmentContent, GetAttachmentPreview
from microchat.api.chats import GetChatMedias, GetChats, GetMessages
from microchat.api.chats import EditMessage, DeleteMessage
from microchat.api.chats import RemoveChatMedia
from microchat.api.chats import SendMessage
from microchat.api_utils.exceptions import BadRequest, NotFound

from microchat.core.entities import Animation, Audio, File, Image, Video
from .misc import get_disposition, get_request_payload, int_param
from .misc import get_access_token, get_media_access_info


MEDIA_CLASSES: dict[str, type[Image | Animation | Audio | Video | File]] = {
    "photo": Image,
    "animation": Animation,
    "audio": Audio,
    "video": Video,
    "file": File
}


async def chats_request_params(request: web.Request) -> GetChats:
    access_token = get_access_token(request)
    disposition = get_disposition(request)
    return GetChats(access_token, disposition)


async def chat_request_params(request: web.Request) -> GetChat:
    access_token = get_access_token(request)
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    if entity_id:
        chat = int_param(entity_id)
        return GetChat(access_token, chat)
    elif alias:
        return GetChat(access_token, alias)
    else:
        raise BadRequest


async def messages_request_params(request: web.Request) -> GetMessages:
    access_token = get_access_token(request)
    chat_request = await chat_request_params(request)
    disposition = get_disposition(request)
    return GetMessages(access_token, chat_request, disposition)


async def message_request_params(request: web.Request) -> GetMessage:
    access_token = get_access_token(request)
    chat_request = await chat_request_params(request)
    message_id_repr = request.match_info.get("message_id", "")
    message_id = int_param(message_id_repr)
    return GetMessage(access_token, chat_request, message_id)


async def message_send_params(request: web.Request) -> SendMessage:
    access_token = get_access_token(request)
    chat_request = await chat_request_params(request)
    payload = await get_request_payload(request)
    text = payload.get("text")
    attachments_ids = payload.get("attachments", [])
    reply_to_id = payload.get("reply_to")
    if attachments_ids and all(isinstance(id, int) for id in attachments_ids):
        raise BadRequest("Attachments must be list of ints")
    if text is None and not attachments_ids:
        raise BadRequest("Message text or attachments must be given")
    if reply_to_id is not None and not isinstance(reply_to_id, int):
        raise BadRequest("'reply_to' must be int")
    return SendMessage(
        access_token, chat_request, text, attachments_ids, reply_to_id
    )


async def message_edit_params(request: web.Request) -> EditMessage:
    access_token = get_access_token(request)
    message_request = await message_request_params(request)
    payload = await get_request_payload(request)
    text = payload.get("text")
    attachments_ids = payload.get("attachments", [])
    if attachments_ids and all(isinstance(id, int) for id in attachments_ids):
        raise BadRequest("Attachments must be list of ints")
    if text is None and not attachments_ids:
        raise BadRequest("Message text or attachments must be given")
    return EditMessage(access_token, message_request, text, attachments_ids)


async def message_delete_params(request: web.Request) -> DeleteMessage:
    access_token = get_access_token(request)
    message_request = await message_request_params(request)
    return DeleteMessage(access_token, message_request)


async def attachment_content_params(
    request: web.Request
) -> GetAttachmentContent:
    access_token, csrf_token = get_media_access_info(request)
    message_request = await message_request_params(request)
    attachment_id_repr = request.match_info.get("attachment_id", "")
    attachment_id = int_param(attachment_id_repr)
    return GetAttachmentContent(
        access_token, csrf_token, message_request, attachment_id
    )


async def attachment_preview_params(
    request: web.Request
) -> GetAttachmentPreview:
    access_token, csrf_token = get_media_access_info(request)
    message_request = await message_request_params(request)
    attachment_id_repr = request.match_info.get("attachment_id", "")
    attachment_id = int_param(attachment_id_repr)
    return GetAttachmentPreview(
        access_token, csrf_token, message_request, attachment_id
    )


async def medias_request_params(request: web.Request) -> GetChatMedias:
    access_token = get_access_token(request)
    chat_request = await chat_request_params(request)
    disposition = get_disposition(request)
    media_type_repr = request.match_info.get("media_type", "")
    media_type = MEDIA_CLASSES.get(media_type_repr)
    if media_type is None:
        raise NotFound(f"Unknown media type: '{media_type_repr}'")
    return GetChatMedias(access_token, chat_request, disposition, media_type)


async def media_request_params(request: web.Request) -> GetChatMedia:
    access_token = get_access_token(request)
    chat_request = await chat_request_params(request)
    media_id_repr = request.match_info.get("media_id", "")
    media_id = int_param(media_id_repr)
    media_type_repr = request.match_info.get("media_type", "")
    media_type = MEDIA_CLASSES.get(media_type_repr)
    if media_type is None:
        raise NotFound(f"Unknown media type: '{media_type_repr}'")
    return GetChatMedia(access_token, chat_request, media_id, media_type)


async def media_delete_params(request: web.Request) -> RemoveChatMedia:
    access_token = get_access_token(request)
    chat_request = await chat_request_params(request)
    media_id_repr = request.match_info.get("media_id", "")
    media_id = int_param(media_id_repr)
    media_type_repr = request.match_info.get("media_type", "")
    media_type = MEDIA_CLASSES.get(media_type_repr)
    if media_type is None:
        raise NotFound(f"Unknown media type: '{media_type_repr}'")
    return RemoveChatMedia(access_token, chat_request, media_id, media_type)
