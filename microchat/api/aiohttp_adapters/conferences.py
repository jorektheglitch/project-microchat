from dataclasses import dataclass

from aiohttp import web

from microchat.api_utils.request import APIRequest
from microchat.api_utils.exceptions import BadRequest
from .misc import Disposition, get_disposition
from .misc import PermissionsPatch, get_permissions_patch
from .misc import get_request_payload, int_param


@dataclass
class CreateConference(APIRequest):
    alias: str | None
    title: str
    avatar: str | None
    description: str | None


@dataclass
class GetConference(APIRequest):
    conference: int | str


@dataclass
class GetDefaultPermissions(APIRequest):
    conference_request: GetConference


@dataclass
class EditDefaultPermissions(APIRequest):
    conference_request: GetConference
    permissions_patch: PermissionsPatch


@dataclass
class GetMembers(APIRequest):
    conference_request: GetConference
    disposition: Disposition


@dataclass
class GetMember(APIRequest):
    conference_request: GetConference
    member: int | str


@dataclass
class AddMember(APIRequest):
    conference_request: GetConference
    invitee: int | str


@dataclass
class RemoveMember(APIRequest):
    member_request: GetMember


@dataclass
class GetMemberPermissions(APIRequest):
    member_request: GetMember


@dataclass
class EditMemberPermissions(APIRequest):
    member_request: GetMember
    permissions_patch: PermissionsPatch


async def conference_request_params(request: web.Request) -> GetConference:
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    if entity_id:
        chat = int_param(entity_id)
        return GetConference(chat)
    elif alias:
        return GetConference(alias)
    else:
        raise BadRequest


async def conference_create_params(request: web.Request) -> CreateConference:
    payload = await get_request_payload(request)
    alias = payload.get("alias")
    title = payload.get("title")
    avatar = payload.get("avatar")
    description = payload.get("description")
    for param in (alias, avatar, description):
        if param is not None and not isinstance(param, str):
            raise BadRequest(
                "'alias', 'avatar' and 'defcription' must be strings"
            )
    if title is None or not isinstance(title, str):
        raise BadRequest("'title' parameter must be string")
    return CreateConference(alias, title, avatar, description)


async def default_permissions_request_params(
    request: web.Request
) -> GetDefaultPermissions:
    conference_request = await conference_request_params(request)
    return GetDefaultPermissions(conference_request)


async def default_permissions_edit_params(
    request: web.Request
) -> EditDefaultPermissions:
    conference_request = await conference_request_params(request)
    payload = await get_request_payload(request)
    permissions_patch = get_permissions_patch(payload)
    return EditDefaultPermissions(conference_request, permissions_patch)


async def members_request_params(request: web.Request) -> GetMembers:
    conference_request = await conference_request_params(request)
    disposition = get_disposition(request)
    return GetMembers(conference_request, disposition)


async def member_request_params(request: web.Request) -> GetMember:
    conference_request = await conference_request_params(request)
    member_id_repr = request.match_info.get("member_id")
    member_alias = request.match_info.get("member_alias")
    if member_id_repr:
        member_id = int_param(member_id_repr)
        return GetMember(conference_request, member_id)
    elif member_alias:
        return GetMember(conference_request, member_alias)
    raise BadRequest


async def member_add_params(request: web.Request) -> AddMember:
    conference_request = await conference_request_params(request)
    payload = await get_request_payload(request)
    invitee_id = payload.get("invitee_id")
    invitee_alias = payload.get("ivitee_alias")
    if isinstance(invitee_id, int):
        return AddMember(conference_request, invitee_id)
    elif isinstance(invitee_alias, str):
        return AddMember(conference_request, invitee_alias)
    else:
        raise BadRequest(
            "'invitee_id' or 'invitee_alias' missing or has invalid type"
        )


async def member_remove_params(request: web.Request) -> RemoveMember:
    member_request = await member_request_params(request)
    return RemoveMember(member_request)


async def member_permissions_request_params(
    request: web.Request
) -> GetMemberPermissions:
    member_request = await member_request_params(request)
    return GetMemberPermissions(member_request)


async def member_permissions_edit_params(
    request: web.Request
) -> EditMemberPermissions:
    member_request = await member_request_params(request)
    payload = await get_request_payload(request)
    permissions_patch = get_permissions_patch(payload)
    return EditMemberPermissions(member_request, permissions_patch)
