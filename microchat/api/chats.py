from dataclasses import dataclass
from typing import AsyncIterable, Sequence

from microchat.api_utils.exceptions import NotFound
from microchat.api_utils.request import AuthenticatedRequest, CookieAuthenticatedRequest
from microchat.api_utils.response import APIResponse, Status
from microchat.api_utils.handler import authenticated, cookie_authenticated

from microchat.core.entities import User, Dialog, ConferenceParticipation
from microchat.core.entities import Message, Attachment
from microchat.core.entities import File, Media
from microchat.core.entities import Animation, Image, Video, Audio
from microchat.services import ServiceSet

from .misc import Disposition


@dataclass
class ChatsAPIRequest(AuthenticatedRequest):
    pass


@dataclass
class GetChats(ChatsAPIRequest):
    disposition: Disposition


@dataclass
class GetChat(ChatsAPIRequest):
    chat: str | int


@dataclass
class GetMessages(ChatsAPIRequest):
    chat: GetChat
    disposition: Disposition


@dataclass
class GetMessage(ChatsAPIRequest):
    chat: GetChat
    message_no: int


@dataclass
class SendMessage(ChatsAPIRequest):
    chat: GetChat
    text: str | None
    attachments: list[str] | None
    reply_to: int | None


@dataclass
class EditMessage(ChatsAPIRequest):
    message: GetMessage
    text: str | None
    attachments: list[str] | None


@dataclass
class DeleteMessage(ChatsAPIRequest):
    message: GetMessage


@dataclass
class GetAttachmentPreview(ChatsAPIRequest, CookieAuthenticatedRequest):
    message: GetMessage
    attachment_no: int


@dataclass
class GetAttachmentContent(ChatsAPIRequest, CookieAuthenticatedRequest):
    message: GetMessage
    attachment_no: int


@dataclass
class GetChatMedias(ChatsAPIRequest):
    chat: GetChat
    disposition: Disposition
    media_type: type[Image | Animation | Audio | Video | File]


@dataclass
class GetChatMedia(ChatsAPIRequest):
    chat: GetChat
    no: int
    media_type: type[Image | Animation | Audio | Video | File]


@dataclass
class RemoveChatMedia(GetChatMedia):
    pass


# @router.get("/")
@authenticated
async def list_chats(
    request: GetChats, services: ServiceSet, user: User
) -> APIResponse[Sequence[Dialog | ConferenceParticipation[User]]]:
    offset = request.disposition.offset
    count = request.disposition.count
    chats = await services.chats.list_chats(user, offset, count)
    return APIResponse(chats)


# @router.get(r"/{entity_id:\d+}")
# @router.get(r"/@{alias:\w+}")
@authenticated
async def get_chat(
    request: GetChat, services: ServiceSet, user: User
) -> APIResponse[Dialog | ConferenceParticipation[User]]:
    chat_identity = request.chat
    chat = await services.agents.get_chat(user, chat_identity)
    return APIResponse(chat)


# @router.get(r"/{entity_id:\d+}/messages")
# @router.get(r"/@{alias:\w+}/messages")
@authenticated
async def list_messages(
    request: GetMessages, services: ServiceSet, user: User
) -> APIResponse[Sequence[Message]]:
    offset = request.disposition.offset
    count = request.disposition.count
    chat_response = await get_chat(request.chat, services, user)
    chat = chat_response.payload
    messages = await services.chats.list_chat_messages(
        user, chat, offset, count
    )
    return APIResponse(messages)


# @router.post(r"/{entity_id:\d+}/messages")
# @router.post(r"/@{alias:\w+}/messages")
@authenticated
async def send_message(
    request: SendMessage, services: ServiceSet, user: User
) -> APIResponse[Message]:
    text = request.text
    reply_to = request.reply_to
    attachments = request.attachments
    chat_response = await get_chat(request.chat, services, user)
    chat = chat_response.payload
    message = await services.chats.add_chat_message(
        user, chat, text, attachments, reply_to
    )
    return APIResponse(message)


# @router.get(r"/{entity_id:\d+}/messages/{id:\d+}")
# @router.get(r"/@{alias:\w+}/messages/{id:\d+}")
@authenticated
async def get_message(
    request: GetMessage, services: ServiceSet, user: User
) -> APIResponse[Message]:
    id = request.message_no
    message_id = int(id)
    chat_response = await get_chat(request.chat, services, user)
    chat = chat_response.payload
    message = await services.chats.get_chat_message(user, chat, message_id)
    return APIResponse(message)


# @router.patch(r"/{entity_id:\d+}/messages/{id:\d+}")
# @router.patch(r"/@{alias:\w+}/messages/{id:\d+}")
@authenticated
async def edit_message(
    request: EditMessage, services: ServiceSet, user: User
) -> APIResponse[Message]:
    message_no = request.message.message_no
    text = request.text
    attachments = request.attachments
    chat_request = request.message.chat
    chat_response = await get_chat(chat_request, services, user)
    chat = chat_response.payload
    edited_message = await services.chats.edit_chat_message(
        user, chat, message_no, text, attachments  # type: ignore
    )
    return APIResponse(edited_message)


# @router.delete(r"/{entity_id:\d+}/messages/{id:\d+}")
# @router.delete(r"/@{alias:\w+}/messages/{id:\d+}")
@authenticated
async def remove_message(
    request: DeleteMessage, services: ServiceSet, user: User
) -> APIResponse[None]:
    message_no = request.message.message_no
    chat_request = request.message.chat
    chat_response = await get_chat(chat_request, services, user)
    chat = chat_response.payload
    await services.chats.remove_chat_message(user, chat, message_no)
    return APIResponse(status=Status.NO_CONTENT)


# @router.get(r"/{entity_id:\d+}/messages/{message_id:\d+}/attachments/{id:\w+}/{view:(preview|content)}")
# @router.get(r"/@{alias:\w+}/messages/{message_id:\d+}/attachments/{id:\w+}/{view:(preview|content)}")
@cookie_authenticated
async def get_attachment_content(
    request: GetAttachmentContent | GetAttachmentPreview,
    services: ServiceSet,
    user: User
) -> APIResponse[AsyncIterable[bytes]]:
    message_response = await get_message(request.message, services, user)
    message = message_response.payload
    attachment = await message.attachments[request.attachment_no]
    media = attachment.media
    if isinstance(request, GetAttachmentPreview):
        if not isinstance(media, (Image, Video, Animation)):
            media_type = type(media).__name__
            raise NotFound(f"Preview for '{media_type}' is unavailable")
        media = media.preview
    content = services.files.iter_content(user, media.file_info)
    return APIResponse(content)


MEDIA_TYPE = r"{media_type:(photo|video|audio|animation|file)s}"


# @router.get(r"/{entity_id:\d+}/messages/" + MEDIA_TYPE)
# @router.get(r"/@{alias:\w+}/messages/" + MEDIA_TYPE)
@authenticated
async def list_chat_media(
    request: GetChatMedias, services: ServiceSet, user: User
) -> APIResponse[Sequence[Attachment[Media]]]:
    media_type = request.media_type
    offset = request.disposition.offset
    count = request.disposition.count
    chat_request = request.chat
    chat_response = await get_chat(chat_request, services, user)
    chat = chat_response.payload
    medias = await services.chats.list_chat_media(
        user, chat, media_type, offset, count
    )
    return APIResponse(medias)


# @router.get(r"/{entity_id:\d+}/messages/" + MEDIA_TYPE + r"/{id:\d+}")
# @router.get(r"/@{alias:\w+}/messages/" + MEDIA_TYPE + r"/{id:\d+}")
@authenticated
async def get_chat_media(
    request: GetChatMedia, services: ServiceSet, user: User
) -> APIResponse[Attachment[Media]]:
    media_type = request.media_type
    no = request.no
    chat_request = request.chat
    chat_response = await get_chat(chat_request, services, user)
    chat = chat_response.payload
    media = await services.chats.get_chat_media(user, chat, media_type, no)
    return APIResponse(media)


# @router.delete(r"/{entity_id:\d+}/messages/" + MEDIA_TYPE + r"/{id:\d+}")
# @router.delete(r"/@{alias:\w+}/messages/" + MEDIA_TYPE + r"/{id:\d+}")
@authenticated
async def remove_chat_media(
    request: RemoveChatMedia, services: ServiceSet, user: User
) -> APIResponse[Attachment[Media]]:
    media_type = request.media_type
    no = request.no
    chat_request = request.chat
    chat_response = await get_chat(chat_request, services, user)
    chat = chat_response.payload
    await services.chats.remove_chat_media(
        user, chat, media_type, no
    )
    return APIResponse(status=Status.NO_CONTENT)
