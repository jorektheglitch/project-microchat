from __future__ import annotations

from abc import ABC
from contextlib import asynccontextmanager

from typing import AsyncGenerator, Iterable, List, TypeVar, overload

from microchat.core.entities import Bot, Conference, User, Actor, Session
from microchat.core.entities import ConferenceParticipation, Dialog
from microchat.core.entities import Permissions
from microchat.core.entities import Message, Attachment, Media, Image
from microchat.core.entities import FileInfo, TempFile, MIME_TUPLES
from microchat.core.jwt_manager import JWTManager
from microchat.core.types import MIMETuple
from microchat.storages import UoW


M = TypeVar("M", bound=Media)

Agent = User | Bot | Conference
A = TypeVar("A", bound=Agent)


class ServiceError(ABC, Exception):
    pass


class AccessDenied(ServiceError):
    pass


class AuthenticationError(ServiceError):
    pass


class InvalidCredentials(AuthenticationError):
    pass


class UnsupportedMethod(AuthenticationError):
    pass


class MissingToken(AuthenticationError):
    pass


class InvalidToken(AuthenticationError):
    pass


class ImageExpected(ServiceError):
    pass


class DoesNotExists(ServiceError):
    pass


class IncompleteMIMEType(ServiceError):
    pass


class UnsupportedMIMEType(ServiceError):
    pass


class ServiceSet:

    auth: Auth
    chats: Chats
    conferences: Conferences
    files: Files
    agents: Agents

    def __init__(self, uow: UoW) -> None:
        pass


class Service(ABC):
    uow: UoW

    def __init__(self, uow: UoW) -> None:
        super().__init__()
        self.uow = uow


class Auth(Service):
    jwt_manager: JWTManager

    async def new_session(self, username: str, password: str) -> str:
        entity = await self.uow.entities.get_by_alias(username)
        if not isinstance(entity, User):
            raise InvalidCredentials()
        auth_info = await self.uow.auth.get_auth_data(entity, "password")
        try:
            auth_succeed = auth_info.check(password.encode())
        except NotImplementedError as e:
            raise UnsupportedMethod(e.args[0])
        if not auth_succeed:
            raise InvalidCredentials()
        session = await self.uow.auth.create_session(entity, auth_info)
        token = self.jwt_manager.create_access_token(entity.id, session.id)
        return token

    async def list_sessions(
        self, user: User, offset: int, count: int
    ) -> List[Session]:
        return list(await user.sessions[offset:offset+count])

    async def get_session(self, user: User, id: int) -> Session:
        session = await user.sessions[id]
        return session

    async def resolve_token(self, token: str) -> Session:
        payload = self.jwt_manager.decode_access_token(token)
        entity = await self.uow.entities.get_by_id(payload["user"])
        if not isinstance(entity, User):
            raise InvalidToken()
        session = await entity.sessions[payload["session"]]
        return session

    async def resolve_media_token(
        self, media_cookie: str, csrf_token: str
    ) -> Session:
        session_info = self.jwt_manager.decode_access_token(media_cookie)
        csrf_info = self.jwt_manager.decode_csrf_token(csrf_token)
        # TODO: add CSRF token checking
        entity = self.uow.entities.get_by_id(session_info["user"])
        if not isinstance(entity, User):
            raise InvalidToken()
        session = await entity.sessions[session_info["session"]]
        return session

    async def terminate_session(self, user: User, session: Session) -> None:
        await self.uow.auth.terminate_session(user, session)


class Agents(Service):

    async def get(
        self, user: User, identity: int | str
    ) -> Agent:
        if isinstance(identity, int):
            entity = await self.uow.entities.get_by_id(identity)
        elif isinstance(identity, str):
            entity = await self.uow.entities.get_by_alias(identity)
        return entity

    async def get_chat(
        self, user: User, identity: int | str
    ) -> Dialog | ConferenceParticipation[User]:
        if isinstance(identity, str):
            related = await self.uow.entities.get_by_alias(identity)
            identity = related.id
        if isinstance(identity, int):
            relation = await self.uow.relations.get_relation(user, identity)
        return relation

    async def list_avatars(
        self, user: User, agent: Agent, offset: int, count: int
    ) -> List[Image]:
        # TODO: check user's access to entity's avatar
        avatars = await agent.avatars[offset:offset+count]
        return list(avatars)

    async def get_avatar(
        self, user: User, agent: Agent, id: int
    ) -> Image:
        # TODO: check user's access to entity's avatar
        avatar = await agent.avatars[id]
        return avatar

    async def edit_self(
        self,
        user: User,
        alias: str | None = None,
        avatar_hash: str | None = None,
        name: str | None = None,
        surname: str | None = None,
        bio: str | None = None
    ) -> User:
        avatar = None
        if avatar_hash is not None:
            avatar = await self.uow.media.get_by_hash(user, avatar_hash)
        if avatar is not None and not isinstance(avatar, Image):
            raise ImageExpected()
        updated = await self.uow.entities.edit_user(
            user, alias, avatar, name, surname, bio
        )
        return updated

    async def edit_permissions(
        self,
        user: User,
        relation: Dialog,
        **kwargs: bool
    ) -> Dialog:
        updated = await self.uow.relations.edit_permissions(
            user, relation, kwargs
        )
        return updated

    async def edit_agent(
        self,
        user: User,
        agent: A,
        **kwargs: str
    ) -> A:
        await self._check_permissions(user, agent)
        updated = await self.uow.entities.edit_entity(agent, kwargs)
        return updated

    async def set_avatar(
        self, user: User, agent: Agent, avatar_hash: str
    ) -> Image:
        await self._check_permissions(user, agent)
        avatar = self.uow.media.get_by_hash(user, avatar_hash)
        if not isinstance(avatar, Image):
            raise ImageExpected()
        await self.uow.entities.set_avatar(agent, avatar)
        return avatar

    async def remove_avatar(
        self, user: User, agent: Agent, id: int
    ) -> None:
        await self._check_permissions(user, agent)
        await self.uow.entities.remove_avatar(agent, id)

    async def _check_permissions(self, user: User, agent: Agent) -> None:
        if isinstance(agent, User) and agent != user:
            raise AccessDenied("Can't edit other users")
        elif isinstance(agent, Bot) and agent.owner != user:
            raise AccessDenied("You are not a bot's owner")
        elif isinstance(agent, Conference):
            relation = await self.get_chat(user, agent.id)
            if not relation.permissions:
                raise AccessDenied("You have not permissions in conference")
            if not relation.permissions.edit_conference:
                raise AccessDenied(
                    "'edit_conference' permission does not granted"
                )

    async def remove_agent(self, user: User, agent: Agent) -> None:
        if isinstance(agent, User) and agent != user:
            raise AccessDenied("Can't delete other users")
        elif isinstance(agent, (Bot, Conference)) and agent.owner != user:
            raise AccessDenied("Only owner can delete bot/conference")
        await self.uow.entities.remove_entity(agent)


class Chats(Service):

    async def list_chats(
        self, user: User, offset: int, count: int
    ) -> list[Dialog | ConferenceParticipation[User]]:
        chats = await self.uow.chats.get_user_chats(user, offset, count)
        return chats

    async def list_chat_messages(
        self,
        user: User, chat: Dialog | ConferenceParticipation[User],
        offset: int, count: int
    ) -> list[Message]:
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
        attachments_hashes: List[str] | None = None
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
    ) -> list[Attachment[M]]:
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


class Conferences(Service):

    async def list_members(
        self, user: User | Bot, conference: Conference,
        offset: int, count: int
    ) -> List[ConferenceParticipation[User | Bot]]:
        if conference.private:
            relation = await self.uow.relations.get_relation(
                user, conference.id
            )
            if isinstance(relation, Dialog):
                raise RuntimeError
            # TODO: somehow check that user is conference member
        members = await self.uow.conferences.list_members(
            conference, offset, count
        )
        return members

    async def get_member(
        self, user: User | Bot, conference: Conference,
        no: int | User | Bot
    ) -> ConferenceParticipation[User | Bot]:
        if isinstance(no, int):
            members = await self.list_members(user, conference, no, 1)
            if not members:
                raise DoesNotExists()
            member = members[0]
            if member.no != no:
                raise DoesNotExists()
        else:
            member = await self.uow.conferences.find_member(conference, no)
        return member

    async def add_member(
        self, user: User, conference: Conference,
        invitee: Actor
    ) -> ConferenceParticipation[Actor]:
        relation = await self.get_member(user, conference, user)
        permissions = relation.permissions or conference.default_permissions
        if not permissions.add_user:
            raise AccessDenied("'add_user' permission does not granted")
        member = await self.uow.conferences.add_member(conference, invitee)
        return member

    async def remove_member(
        self, user: User, conference: Conference,
        no: int | User | Bot
    ) -> None:
        relation = await self.get_member(user, conference, user)
        permissions = relation.permissions or conference.default_permissions
        if not permissions.remove_user:
            raise AccessDenied("'remove_user' permission does not granted")
        member = await self.get_member(user, conference, no)
        await self.uow.conferences.remove_member(member)

    async def get_member_permissions(
        self, user: User | Bot, conference: Conference,
        no: int | User | Bot
    ) -> Permissions:
        # TODO: somehow check that user is conference member
        member = await self.get_member(user, conference, no)
        permissions = member.permissions or conference.default_permissions
        return permissions

    async def edit_member_permissions(
        self,
        user: User | Bot, conference: Conference,
        no: int | User | Bot,
        read: bool | None = None,
        send: bool | None = None,
        delete: bool | None = None,
        send_media: bool | None = None,
        send_mediamessage: bool | None = None,
        add_user: bool | None = None,
        pin_message: bool | None = None,
        edit_conference: bool | None = None,
    ) -> Permissions:
        relation = await self.get_member(user, conference, user)
        user_perms = relation.permissions or conference.default_permissions
        if not user_perms.remove_user:
            raise AccessDenied("'remove_user' permission does not granted")
        member = await self.get_member(user, conference, no)
        # TODO: do something with this creepy part of code
        permissions = member.permissions or conference.default_permissions
        permissions.read = read or permissions.read
        permissions.send = send or permissions.send
        permissions.delete = delete or permissions.delete
        permissions.send_media = send_media or permissions.send_media
        permissions.send_mediamessage = send_mediamessage or permissions.send_mediamessage  # noqa
        permissions.add_user = add_user or permissions.add_user
        permissions.pin_message = pin_message or permissions.pin_message
        permissions.edit_conference = edit_conference or permissions.edit_conference  # noqa
        updated = await self.uow.conferences.update_permissions(
            member, permissions
        )
        return updated


class Files(Service):

    async def get_info(self, user: User, hash: str) -> Media:
        return await self.uow.media.get_by_hash(user, hash)

    async def get_infos(
        self, user: User, hashes: Iterable[str]
    ) -> List[Media]:
        return await self.uow.media.get_by_hashes(user, hashes)

    async def iter_content(
        self,
        user: User,
        file: FileInfo,
        *,
        chunk_size: int = 1024**2
    ) -> AsyncGenerator[bytes, None]:
        reader = await self.uow.media.open(file)
        chunk = await reader.read(chunk_size)
        while chunk:
            yield chunk
            chunk = await reader.read(chunk_size)

    async def materialize(
        self, user: User, file: TempFile, name: str, mime_repr: str
    ) -> Media:
        mime = self._parse_mime_repr(mime_repr)
        media = await self.uow.media.save_media(user, file, name, mime)
        return media

    @asynccontextmanager
    async def tempfile(self) -> AsyncGenerator[TempFile, None]:
        tempfile = await self.uow.media.create_tempfile()
        try:
            yield tempfile
        finally:
            await tempfile.close()

    @staticmethod
    def _parse_mime_repr(mime_repr: str) -> MIMETuple:
        mime_repr_ = mime_repr.split("/", maxsplit=1)
        mime_tuple = MIME_TUPLES.get(tuple(mime_repr_))  # type: ignore
        if mime_tuple is None:
            raise UnsupportedMIMEType()
        return mime_tuple
