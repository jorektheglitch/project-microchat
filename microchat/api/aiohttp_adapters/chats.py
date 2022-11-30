from dataclasses import dataclass

from aiohttp import web
from microchat.api_utils.exceptions import BadRequest, NotFound

from microchat.api_utils.request import APIRequest
from microchat.core.entities import Animation, Audio, File, Image, Video
from .misc import Disposition, get_disposition, get_request_payload, int_param


MEDIA_CLASSES: dict[str, type[Image | Animation | Audio | Video | File]] = {
    "photo": Image,
    "animation": Animation,
    "audio": Audio,
    "video": Video,
    "file": File
}


@dataclass
class ChatsAPIRequest(APIRequest):
    pass


@dataclass
class GetChats(ChatsAPIRequest):
    disposition: Disposition


@dataclass
class GetChat(ChatsAPIRequest):
    chat: str | int


@dataclass
class GetMessages(ChatsAPIRequest):
    chat_request: GetChat
    disposition: Disposition


@dataclass
class GetMessage(ChatsAPIRequest):
    chat_request: GetChat
    message_id: int


@dataclass
class SendMessage(ChatsAPIRequest):
    chat_request: GetChat
    text: str | None
    attachments: list[int] | None
    reply_to: int | None


@dataclass
class EditMessage(ChatsAPIRequest):
    message_request: GetMessage
    text: str | None
    attachments: list[int] | None


@dataclass
class DeleteMessage(ChatsAPIRequest):
    message_request: GetMessage


@dataclass
class GetAttachmentPreview(ChatsAPIRequest):
    message_request: GetMessage
    attachment_id: int


@dataclass
class GetAttachmentContent(ChatsAPIRequest):
    message_request: GetMessage
    attachment_id: int


@dataclass
class GetChatMedias(ChatsAPIRequest):
    chat_requset: GetChat
    disposition: Disposition
    media_type: type[Image | Animation | Audio | Video | File]


@dataclass
class ChatMediaRequest(ChatsAPIRequest):
    chat_request: GetChat
    media_id: int
    media_type: type[Image | Animation | Audio | Video | File]


async def chats_request_params(request: web.Request) -> GetChats:
    disposition = get_disposition(request)
    return GetChats(disposition)


async def chat_request_params(request: web.Request) -> GetChat:
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    if entity_id:
        chat = int_param(entity_id)
        return GetChat(chat)
    elif alias:
        return GetChat(alias)
    else:
        raise BadRequest


async def messages_request_params(request: web.Request) -> GetMessages:
    chat_request = await chat_request_params(request)
    disposition = get_disposition(request)
    return GetMessages(chat_request, disposition)


async def message_request_params(request: web.Request) -> GetMessage:
    chat_request = await chat_request_params(request)
    message_id_repr = request.match_info.get("message_id", "")
    message_id = int_param(message_id_repr)
    return GetMessage(chat_request, message_id)


async def message_send_params(request: web.Request) -> SendMessage:
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
    return SendMessage(chat_request, text, attachments_ids, reply_to_id)


async def message_edit_params(request: web.Request) -> EditMessage:
    message_request = await message_request_params(request)
    payload = await get_request_payload(request)
    text = payload.get("text")
    attachments_ids = payload.get("attachments", [])
    if attachments_ids and all(isinstance(id, int) for id in attachments_ids):
        raise BadRequest("Attachments must be list of ints")
    if text is None and not attachments_ids:
        raise BadRequest("Message text or attachments must be given")
    return EditMessage(message_request, text, attachments_ids)


async def message_delete_params(request: web.Request) -> DeleteMessage:
    message_request = await message_request_params(request)
    return DeleteMessage(message_request)


async def attachment_content_params(
    request: web.Request
) -> GetAttachmentContent:
    message_request = await message_request_params(request)
    attachment_id_repr = request.match_info.get("attachment_id", "")
    attachment_id = int_param(attachment_id_repr)
    return GetAttachmentContent(message_request, attachment_id)


async def attachment_preview_params(
    request: web.Request
) -> GetAttachmentPreview:
    message_request = await message_request_params(request)
    attachment_id_repr = request.match_info.get("attachment_id", "")
    attachment_id = int_param(attachment_id_repr)
    return GetAttachmentPreview(message_request, attachment_id)


async def medias_request_params(request: web.Request) -> GetChatMedias:
    chat_request = await chat_request_params(request)
    disposition = get_disposition(request)
    media_type_repr = request.match_info.get("media_type", "")
    media_type = MEDIA_CLASSES.get(media_type_repr)
    if media_type is None:
        raise NotFound(f"Unknown media type: '{media_type_repr}'")
    return GetChatMedias(chat_request, disposition, media_type)


async def media_request_params(request: web.Request) -> ChatMediaRequest:
    chat_request = await chat_request_params(request)
    media_id_repr = request.match_info.get("media_id", "")
    media_id = int_param(media_id_repr)
    media_type_repr = request.match_info.get("media_type", "")
    media_type = MEDIA_CLASSES.get(media_type_repr)
    if media_type is None:
        raise NotFound(f"Unknown media type: '{media_type_repr}'")
    return ChatMediaRequest(chat_request, media_id, media_type)
