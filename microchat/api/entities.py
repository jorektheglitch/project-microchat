from dataclasses import dataclass

from typing import cast

from microchat.services import ServiceSet
from microchat.core.entities import User, Bot, ConferenceParticipation
from microchat.core.entities import Conference, Permissions
from microchat.core.entities import Image

from microchat.api_utils.request import APIRequest, Authenticated
from microchat.api_utils.response import APIResponse, Status
from microchat.api_utils.exceptions import BadRequest
from microchat.api_utils.handler import authenticated

from .misc import Disposition, PermissionsPatch


@dataclass
class EntitiesAPIRequest(APIRequest, Authenticated):
    pass


@dataclass
class GetSelf(EntitiesAPIRequest):
    pass


@dataclass
class EditSelf(EntitiesAPIRequest):
    alias: str | None
    name: str | None
    surname: str | None
    bio: str | None
    avatar: str | None


@dataclass
class RemoveSelf(EntitiesAPIRequest):
    pass


@dataclass
class GetEntity(EntitiesAPIRequest):
    identity: str | int


@dataclass
class EditEntity(EntitiesAPIRequest):
    entity_request: GetEntity
    update: dict[str, str]


@dataclass
class RemoveEntity(EntitiesAPIRequest):
    entity_request: GetEntity


@dataclass
class GetAvatars(EntitiesAPIRequest):
    entity_request: GetEntity
    disposition: Disposition


@dataclass
class GetAvatar(EntitiesAPIRequest):
    entity_request: GetEntity
    avatar_no: int


@dataclass
class SetAvatar(EntitiesAPIRequest):
    entity_request: GetEntity
    image_hash: str


@dataclass
class RemoveAvatar(GetAvatar):
    pass


@dataclass
class GetPermissions(EntitiesAPIRequest):
    entity_request: GetEntity


@dataclass
class EditPermissions(EntitiesAPIRequest):
    entity_request: GetEntity
    permissions_patch: PermissionsPatch


# @router.get("/self")
@authenticated
async def get_self(
    request: GetSelf, services: ServiceSet, user: User
) -> APIResponse[User]:
    return APIResponse(user)


# @router.patch("/self")
@authenticated
async def edit_self(
    request: EditSelf, services: ServiceSet, user: User
) -> APIResponse[User]:
    alias = request.alias
    avatar = request.avatar
    name = request.name
    surname = request.surname
    bio = request.bio
    updated = await services.agents.edit_self(
        user, alias, avatar, name, surname, bio
    )
    return APIResponse(updated)


# @router.delete("/self")
@authenticated
async def remove_self(
    request: RemoveSelf, services: ServiceSet, user: User
) -> APIResponse[None]:
    await services.agents.remove_agent(user, user)
    return APIResponse(status=Status.NO_CONTENT)


# @router.get(r"/{entity_id:\d+}")
# @router.get(r"/@{alias:\w+}")
@authenticated
async def get_entity(
    request: GetEntity, services: ServiceSet, user: User
) -> APIResponse[User | Bot | Conference]:
    identity = request.identity
    entity = await services.agents.get(user, identity)
    return APIResponse(entity)


# @router.patch(r"/{entity_id:\d+}")
# @router.patch(r"/@{alias:\w+}")
@authenticated
async def edit_entity(
    request: EditEntity, services: ServiceSet, user: User
) -> APIResponse[User | Bot | Conference]:
    entity_response = await get_entity(request.entity_request, services, user)
    entity = entity_response.payload
    overlays = request.update
    updated = await services.agents.edit_agent(user, entity, **overlays)
    return APIResponse(updated)


# @router.get(r"/{entity_id:\d+}")
@authenticated
async def remove_entity(
    request: RemoveEntity, services: ServiceSet, user: User
) -> APIResponse[None]:
    entity_response = await get_entity(request.entity_request, services, user)
    entity = entity_response.payload
    await services.agents.remove_agent(user, entity)
    return APIResponse(status=Status.NO_CONTENT)


# @router.get(r"/{entity_id:\d+}/avatars")
# @router.get(r"/@{alias:\w+}/avatars")
@authenticated
async def list_entity_avatars(
    request: GetAvatars, services: ServiceSet, user: User
) -> APIResponse[list[Image]]:
    offset = request.disposition.offset
    count = request.disposition.count
    entity_response = await get_entity(request.entity_request, services, user)
    entity = entity_response.payload
    avatars = await services.agents.list_avatars(user, entity, offset, count)
    return APIResponse(avatars)


# @router.get(r"/{entity_id:\d+}/avatars/{id:\d+}")
# @router.get(r"/@{alias:\w+}/avatars/{id:\d+}")
@authenticated
async def get_entity_avatar(
    request: GetAvatar, services: ServiceSet, user: User
) -> APIResponse[Image]:
    avatar_no = request.avatar_no
    entity_response = await get_entity(request.entity_request, services, user)
    entity = entity_response.payload
    avatar = await services.agents.get_avatar(user, entity, avatar_no)
    return APIResponse(avatar)


# @router.post(r"/@{alias:\w+}/avatars")
@authenticated
async def set_entity_avatar(
    request: SetAvatar, services: ServiceSet, user: User
) -> APIResponse[Image]:
    entity_response = await get_entity(request.entity_request, services, user)
    entity = entity_response.payload
    avatar_hash = request.image_hash
    avatar = await services.agents.set_avatar(user, entity, avatar_hash)
    return APIResponse(avatar)


# @router.delete(r"/@{alias:\w+}/avatars/{id:\d+}")
@authenticated
async def remove_entity_avatar(
    request: RemoveAvatar, services: ServiceSet, user: User
) -> APIResponse[None]:
    avatar_no = request.avatar_no
    entity_response = await get_entity(request.entity_request, services, user)
    entity = entity_response.payload
    await services.agents.remove_avatar(user, entity, avatar_no)
    return APIResponse(status=Status.NO_CONTENT)


# @router.get(r"/{entity_id:\d+}/permissions")
# @router.get(r"/@{alias:\w+}/permissions")
@authenticated
async def get_entity_permissions(
    request: GetPermissions, services: ServiceSet, user: User
) -> APIResponse[Permissions]:
    identity = request.entity_request.identity
    relation = await services.agents.get_chat(user, identity)
    if isinstance(relation, ConferenceParticipation):
        raise BadRequest("Can't ask for conference's permissions")
    return APIResponse(relation.permissions)


# @router.patch(r"/{entity_id:\d+}/permissions")
# @router.patch(r"/@{alias:\w+}/permissions")
@authenticated
async def edit_entity_permissions(
    request: EditPermissions, services: ServiceSet, user: User
) -> APIResponse[Permissions]:
    identity = request.entity_request.identity
    relation = await services.agents.get_chat(user, identity)
    if isinstance(relation, ConferenceParticipation):
        raise BadRequest("Can't ask for conference's permissions")
    overlay = cast(dict[str, bool], {
        key: value
        for key, value in request.permissions_patch.items()
        if value is not None
    })
    await services.agents.edit_permissions(user, relation, **overlay)
    return APIResponse(relation.permissions)
