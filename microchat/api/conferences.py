from dataclasses import dataclass
from typing import Sequence

from microchat.core.entities import User, Dialog, ConferenceParticipation
from microchat.core.entities import Bot, Conference, Permissions

from microchat.services import ServiceSet
from microchat.api_utils.handler import authenticated
from microchat.api_utils.request import AuthenticatedRequest
from microchat.api_utils.response import APIResponse, Status
from microchat.api_utils.exceptions import BadRequest, NotFound

from .misc import Disposition, PermissionsPatch


@dataclass
class ConferencesAPIRequest(AuthenticatedRequest):
    pass


@dataclass
class CreateConference(ConferencesAPIRequest):
    alias: str | None
    title: str
    avatar: str | None
    description: str | None


@dataclass
class GetConference(ConferencesAPIRequest):
    identity: int | str


@dataclass
class GetDefaultPermissions(ConferencesAPIRequest):
    conference_request: GetConference


@dataclass
class EditDefaultPermissions(ConferencesAPIRequest):
    conference_request: GetConference
    permissions_patch: PermissionsPatch


@dataclass
class GetMembers(ConferencesAPIRequest):
    conference_request: GetConference
    disposition: Disposition


@dataclass
class GetMember(ConferencesAPIRequest):
    conference_request: GetConference
    member_no: int


@dataclass
class AddMember(ConferencesAPIRequest):
    conference_request: GetConference
    invitee: int | str


@dataclass
class RemoveMember(ConferencesAPIRequest):
    member_request: GetMember


@dataclass
class GetMemberPermissions(ConferencesAPIRequest):
    member_request: GetMember


@dataclass
class EditMemberPermissions(ConferencesAPIRequest):
    member_request: GetMember
    permissions_patch: PermissionsPatch


async def get_conference(
    services: ServiceSet, user: User, identity: str | int
) -> Conference:
    relation = await services.agents.get_chat(user, identity)
    if isinstance(relation, Dialog):
        raise NotFound
    return relation.related


async def get_actor(
    services: ServiceSet, user: User, identity: str | int
) -> User | Bot:
    entity = await services.agents.get(user, identity)
    if isinstance(entity, Conference):
        raise BadRequest
    return entity


# @router.get(r"/{entity_id:\d+}/members")
# @router.get(r"/@{alias:\w+}/members")
@authenticated
async def list_chat_members(
    request: GetMembers, services: ServiceSet, user: User
) -> APIResponse[Sequence[ConferenceParticipation[User | Bot]]]:
    identity = request.conference_request.identity
    offset = request.disposition.offset
    count = request.disposition.count
    conference = await get_conference(services, user, identity)
    members = await services.conferences.list_members(
        user, conference, offset, count
    )
    return APIResponse(members)


# @router.post(r"/{entity_id:\d+}/members")
# @router.post(r"/@{alias:\w+}/members")
@authenticated
async def add_chat_member(
    request: AddMember, services: ServiceSet, user: User
) -> APIResponse[ConferenceParticipation[User | Bot]]:
    conference_identity = request.conference_request.identity
    conference = await get_conference(services, user, conference_identity)
    invitee = await get_actor(services, user, request.invitee)
    member = await services.conferences.add_member(
        user, conference, invitee
    )
    return APIResponse(member, Status.CREATED)


# @router.get(r"/{entity_id:\d+}/members/{id:\d+}")
# @router.get(r"/{entity_id:\d+}/members/{member_alias:\w+}")
# @router.get(r"/@{alias:\w+}/members/{id:\d+}")
# @router.get(r"/@{alias:\w+}/members/{member_alias:\w+}")
@authenticated
async def get_chat_member(
    request: GetMember, services: ServiceSet, user: User
) -> APIResponse[ConferenceParticipation[User | Bot]]:
    conference_identity = request.conference_request.identity
    member_no = request.member_no
    conference = await get_conference(services, user, conference_identity)
    member = await services.conferences.get_member(
        user, conference, member_no
    )
    return APIResponse(member)


# @router.delete(r"/{entity_id:\d+}/members/{id:\d+}")
# @router.delete(r"/{entity_id:\d+}/members/{member_alias:\w+}")
# @router.delete(r"/@{alias:\w+}/members/{id:\d+}")
# @router.delete(r"/@{alias:\w+}/members/{member_alias:\w+}")
@authenticated
async def remove_chat_member(
    request: RemoveMember, services: ServiceSet, user: User
) -> APIResponse[None]:
    member_request = request.member_request
    conference_identity = member_request.conference_request.identity
    member_no = member_request.member_no
    conference = await get_conference(services, user, conference_identity)
    await services.conferences.remove_member(user, conference, member_no)
    return APIResponse(status=Status.NO_CONTENT)


# @router.get(r"/{entity_id:\d+}/members/{id:\d+}/permissions")
# @router.get(r"/{entity_id:\d+}/members/{member_alias:\w+}/permissions")
# @router.get(r"/@{alias:\w+}/members/{id:\d+}/permissions")
# @router.get(r"/@{alias:\w+}/members/{member_alias:\w+}/permissions")
@authenticated
async def get_chat_member_permissions(
    request: GetMemberPermissions, services: ServiceSet, user: User
) -> APIResponse[Permissions]:
    member_request = request.member_request
    conference_identity = member_request.conference_request.identity
    member_no = member_request.member_no
    conference = await get_conference(services, user, conference_identity)
    permissions = await services.conferences.get_member_permissions(
        user, conference, member_no
    )
    return APIResponse(permissions)


# @router.patch(r"/{entity_id:\d+}/members/{id:\d+}/permissions")
# @router.patch(r"/{entity_id:\d+}/members/{member_alias:\w+}/permissions")
# @router.patch(r"/@{alias:\w+}/members/{id:\d+}/permissions")
# @router.patch(r"/@{alias:\w+}/members/{member_alias:\w+}/permissions")
@authenticated
async def edit_chat_member_permissions(
    request: EditMemberPermissions, services: ServiceSet, user: User
) -> APIResponse[Permissions]:
    member_request = request.member_request
    conference_identity = member_request.conference_request.identity
    member_no = member_request.member_no
    conference = await get_conference(services, user, conference_identity)
    permissions_update = request.permissions_patch
    permissions = await services.conferences.edit_member_permissions(
        user, conference, member_no, **permissions_update
    )
    return APIResponse(permissions)
