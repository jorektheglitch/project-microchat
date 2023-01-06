from __future__ import annotations

from typing import List, TypeVar

from microchat.core.entities import Bot, Conference, User
from microchat.core.entities import ConferenceParticipation, Dialog
from microchat.core.entities import Image


from .base_service import Service
from .general_exceptions import ServiceError, AccessDenied


Agent = User | Bot | Conference
A = TypeVar("A", bound=Agent)


class ImageExpected(ServiceError):
    pass


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
