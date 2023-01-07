from __future__ import annotations

from microchat.core.entities import Bot, Conference, User, Actor
from microchat.core.entities import ConferenceParticipation, Dialog
from microchat.core.entities import Permissions

from .base_service import Service
from .general_exceptions import DoesNotExists, AccessDenied


class Conferences(Service):

    async def list_members(
        self, user: User | Bot, conference: Conference,
        offset: int, count: int
    ) -> list[ConferenceParticipation[User | Bot]]:
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
