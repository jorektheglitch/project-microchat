from __future__ import annotations

from typing import Sequence, TypeVar, overload

from microchat.core.entities import User
from microchat.core.entities import ConferenceParticipation, Dialog
from microchat.core.entities import Media
from microchat.core.entities import Message, Attachment

from .base_service import Service
from .general_exceptions import AccessDenied, DoesNotExists


M = TypeVar("M", bound=Media)


class Chats(Service):

    async def list_chats(
        self, user: User, offset: int, count: int
    ) -> Sequence[Dialog | ConferenceParticipation[User]]:
        chats = await self.uow.chats.get_user_chats(user, offset, count)
        return chats

    async def list_chat_messages(
        self,
        user: User, chat: Dialog | ConferenceParticipation[User],
        offset: int, count: int
    ) -> Sequence[Message]:
        chats = self.uow.chats
        if isinstance(chat, Dialog):
            messages = await chats.get_dialog_messages(
                user, chat, offset, count
            )
        elif isinstance(chat, ConferenceParticipation):
            if chat.related.private:
                presences = chat.presences
                messages = await chats.get_private_conference_messages(
                    user, chat, offset, count, presences
                )
            else:
                messages = await chats.get_conference_messages(
                    user, chat, offset, count
                )
        return messages

    async def get_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User], no: int
    ) -> Message:
        messages = await self.list_chat_messages(user, chat, no, 1)
        if not messages:
            raise DoesNotExists()
        message = messages[0]
        if message.no != no:
            raise DoesNotExists()
        return message

    @overload
    async def add_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        text: str, attachments_hashes: None, reply_to_no: int | None
    ) -> Message: ...
    @overload  # noqa
    async def add_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        text: str, attachments_hashes: list[str], reply_to_no: int | None
    ) -> Message: ...
    @overload  # noqa
    async def add_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        text: None, attachments_hashes: list[str], reply_to_no: int | None
    ) -> Message: ...
    @overload  # noqa
    async def add_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        text: str | None, attachments_hashes: list[str] | None,
        reply_to_no: int | None
    ) -> Message: ...

    async def add_chat_message(
        self,
        user: User,
        chat: Dialog | ConferenceParticipation[User],
        text: str | None = None,
        attachments_hashes: list[str] | None = None,
        reply_to_no: int | None = None
    ) -> Message:
        if isinstance(chat, ConferenceParticipation):
            # TODO: check that user is conference member
            pass
        permissions = chat.permissions or chat.related.default_permissions
        if not permissions.send:
            raise AccessDenied("Can't send message due to chat restrictions")
        if attachments_hashes and not permissions.send_media:
            raise AccessDenied(
                "Can't send message with attachments due to chat restrictions"
            )
        reply_to = None
        if reply_to_no is not None:
            reply_to = await self.get_chat_message(user, chat, reply_to_no)
        attachments = None
        if attachments_hashes:
            attachments = await self.uow.media.get_by_hashes(
                user, attachments_hashes
            )
        message = await self.uow.chats.add_message(
            user, chat, text, attachments, reply_to
        )
        return message

    @overload
    async def edit_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        no: int, text: str, attachments_hashes: None
    ) -> Message: ...
    @overload  # noqa
    async def edit_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        no: int, text: str, attachments_hashes: list[str]
    ) -> Message: ...
    @overload  # noqa
    async def edit_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        no: int, text: None, attachments_hashes: list[str]
    ) -> Message: ...

    async def edit_chat_message(
        self,
        user: User,
        chat: Dialog | ConferenceParticipation[User],
        no: int,
        text: str | None = None,
        attachments_hashes: list[str] | None = None
    ) -> Message:
        message = await self.get_chat_message(user, chat, no)
        sender = await message.sender
        if sender != user:
            raise AccessDenied("Can't edit other user's messages")
        attachments = None
        if attachments_hashes:
            attachments = await self.uow.media.get_by_hashes(
                user, attachments_hashes
            )
        updated = await self.uow.chats.edit_message(message, text, attachments)
        return updated

    async def remove_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User], no: int
    ) -> None:
        permissions = chat.permissions or chat.related.default_permissions
        message = await self.get_chat_message(user, chat, no)
        sender = await message.sender
        if sender != user and not permissions.delete:
            raise AccessDenied("Can't delete other user's messages")
        await self.uow.chats.remove_message(message)

    async def list_chat_media(
        self,
        user: User, chat: Dialog | ConferenceParticipation[User],
        media_type: type[M],
        offset: int, count: int
    ) -> Sequence[Attachment[M]]:
        chats = self.uow.chats
        if isinstance(chat, Dialog):
            medias = await chats.get_dialog_medias(
                user, chat, media_type, offset, count
            )
        elif isinstance(chat, ConferenceParticipation):
            if chat.related.private:
                presences = chat.presences
                medias = await chats.get_private_conference_medias(
                    user, chat, media_type, offset, count, presences
                )
            else:
                medias = await chats.get_conference_medias(
                    user, chat, media_type, offset, count
                )
        return medias

    async def get_chat_media(
        self,
        user: User, chat: Dialog | ConferenceParticipation[User],
        media_type: type[M],
        no: int
    ) -> Attachment[M]:
        attachments = await self.list_chat_media(user, chat, media_type, no, 1)
        if not attachments:
            raise DoesNotExists()
        attachment = attachments[0]
        if attachment.no != no:
            raise DoesNotExists()
        return attachment

    async def remove_chat_media(
        self,
        user: User, chat: Dialog | ConferenceParticipation[User],
        media_type: type[M],
        no: int
    ) -> None:
        permissions = chat.permissions or chat.related.default_permissions
        attachment = await self.get_chat_media(user, chat, media_type, no)
        sender = attachment.media.loaded_by
        if sender != user and not permissions.delete:
            raise AccessDenied("Can't delete other user's medias")
        await self.uow.chats.remove_media(attachment)
