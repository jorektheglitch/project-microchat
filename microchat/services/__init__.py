from __future__ import annotations

from abc import ABC
from contextlib import asynccontextmanager

from typing import AsyncGenerator, Iterable, List, TypeVar, overload

from microchat.core.entities import Bot, Conference, User, Actor, Session
from microchat.core.entities import ConferenceParticipation, Dialog
from microchat.core.entities import Permissions
from microchat.core.entities import Message, Attachment, Media, Image
from microchat.core.entities import FileInfo, TempFile
from microchat.core.jwt_manager import JWTManager
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


class InvalidToken(AuthenticationError):
    pass


class ImageExpected(ServiceError):
    pass


class DoesNotExists(ServiceError):
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
        self, user: User, id: int
    ) -> Agent:
        return await self.uow.entities.get_by_id(id)

    async def resolve_alias(
        self, user: User, alias: str
    ) -> Agent:
        return await self.uow.entities.get_by_alias(alias)

    async def get_chat(
        self, user: User, id: int
    ) -> Dialog | ConferenceParticipation[User]:
        relation = await self.uow.relations.get_relation(user, id)
        return relation

    async def resolve_chat_alias(
        self, user: User, alias: str
    ) -> Dialog | ConferenceParticipation[User]:
        related = await self.uow.entities.get_by_alias(alias)
        relation = await self.uow.relations.get_relation(user, related.id)
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
    ) -> None:
        await self._check_permissions(user, agent)
        avatar = self.uow.media.get_by_hash(user, avatar_hash)
        if not isinstance(avatar, Image):
            raise ImageExpected()
        await self.uow.entities.set_avatar(agent, avatar)

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
        text: str, attachments: None, reply_to_no: int | None
    ) -> Message: ...
    @overload  # noqa
    async def add_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        text: str, attachments: list[Media], reply_to_no: int | None
    ) -> Message: ...
    @overload  # noqa
    async def add_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        text: None, attachments: list[Media], reply_to_no: int | None
    ) -> Message: ...

    async def add_chat_message(
        self,
        user: User,
        chat: Dialog | ConferenceParticipation[User],
        text: str | None = None,
        attachments: list[Media] | None = None,
        reply_to_no: int | None = None
    ) -> Message:
        if isinstance(chat, ConferenceParticipation):
            # TODO: check that user is conference member
            pass
        permissions = chat.permissions or chat.related.default_permissions
        if not permissions.send:
            raise AccessDenied("Can't send message due to chat restrictions")
        if attachments and not permissions.send_media:
            raise AccessDenied(
                "Can't send message with attachments due to chat restrictions"
            )
        reply_to = None
        if reply_to_no is not None:
            reply_to = await self.get_chat_message(user, chat, reply_to_no)
        message = await self.uow.chats.add_message(
            user, chat, text, attachments, reply_to
        )
        return message

    @overload
    async def edit_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        no: int, text: str, attachments: None
    ) -> Message: ...
    @overload  # noqa
    async def edit_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        no: int, text: str, attachments: List[Media]
    ) -> Message: ...
    @overload  # noqa
    async def edit_chat_message(
        self, user: User, chat: Dialog | ConferenceParticipation[User],
        no: int, text: None, attachments: List[Media]
    ) -> Message: ...

    async def edit_chat_message(
        self,
        user: User,
        chat: Dialog | ConferenceParticipation[User],
        no: int,
        text: str | None = None,
        attachments: List[Media] | None = None
    ) -> Message:
        message = await self.get_chat_message(user, chat, no)
        sender = await message.sender
        if sender != user:
            raise AccessDenied("Can't edit other user's messages")
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

    async def list_chat_members(
        self, user: User | Bot, conference: Conference,
        offset: int, count: int
    ) -> List[ConferenceParticipation[User | Bot]]:
        pass

    async def get_chat_member(
        self, user: User | Bot, conference: Conference,
        no: int | User | Bot
    ) -> ConferenceParticipation[User | Bot]:
        pass

    async def add_chat_member(
        self, user: User, conference: Conference,
        invitee: Actor
    ) -> ConferenceParticipation[Actor]:
        pass

    async def remove_chat_member(
        self, user: User, conference: Conference,
        id: int | User | Bot
    ) -> None:
        pass

    async def get_chat_member_permissions(
        self, user: User | Bot, conference: Conference,
        no: int | User | Bot
    ) -> Permissions:
        pass

    async def edit_chat_member_permissions(
        self, user: User | Bot, conference: Conference,
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
        pass


class Files(Service):

    async def materialize(
        self,
        user: User,
        file: TempFile,
        name: str,
        mime_type: str
    ) -> Media:
        pass

    async def get_info(self, user: User, hash: str) -> Media:
        pass

    async def get_infos(self, user: User, ids: Iterable[int]) -> List[Media]:
        pass

    async def iter_content(
        self,
        user: User,
        file: FileInfo,
        *,
        chunk_size: int = 1024**2
    ) -> AsyncGenerator[bytes, None]:
        yield

    @asynccontextmanager
    async def tempfile(self) -> AsyncGenerator[TempFile, None]:
        tmpfile: TempFile
        try:
            yield tmpfile
        finally:
            await tmpfile.close()
