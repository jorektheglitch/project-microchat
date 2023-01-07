from aiohttp import web

from microchat.api.conferences import GetConference, CreateConference
from microchat.api.conferences import GetDefaultPermissions, EditDefaultPermissions
from microchat.api.conferences import GetMembers, GetMember, AddMember, RemoveMember
from microchat.api.conferences import GetMemberPermissions, EditMemberPermissions
from microchat.api_utils.exceptions import BadRequest

from .misc import get_disposition, get_permissions_patch
from .misc import get_request_payload, int_param
from .misc import get_access_token


async def conference_request_params(request: web.Request) -> GetConference:
    access_token = get_access_token(request)
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    if entity_id:
        chat = int_param(entity_id)
        return GetConference(access_token, chat)
    elif alias:
        return GetConference(access_token, alias)
    else:
        raise BadRequest


async def conference_create_params(request: web.Request) -> CreateConference:
    access_token = get_access_token(request)
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
    return CreateConference(access_token, alias, title, avatar, description)


async def default_permissions_request_params(
    request: web.Request
) -> GetDefaultPermissions:
    access_token = get_access_token(request)
    conference_request = await conference_request_params(request)
    return GetDefaultPermissions(access_token, conference_request)


async def default_permissions_edit_params(
    request: web.Request
) -> EditDefaultPermissions:
    access_token = get_access_token(request)
    conference_request = await conference_request_params(request)
    payload = await get_request_payload(request)
    permissions_patch = get_permissions_patch(payload)
    return EditDefaultPermissions(
        access_token, conference_request, permissions_patch
    )


async def members_request_params(request: web.Request) -> GetMembers:
    access_token = get_access_token(request)
    conference_request = await conference_request_params(request)
    disposition = get_disposition(request)
    return GetMembers(access_token, conference_request, disposition)


async def member_request_params(request: web.Request) -> GetMember:
    access_token = get_access_token(request)
    conference_request = await conference_request_params(request)
    member_no_repr = request.match_info.get("member_no")
    if not member_no_repr:
        raise BadRequest
    member_no = int(member_no_repr)
    return GetMember(access_token, conference_request, member_no)


async def member_add_params(request: web.Request) -> AddMember:
    access_token = get_access_token(request)
    conference_request = await conference_request_params(request)
    payload = await get_request_payload(request)
    invitee_id = payload.get("invitee_id")
    invitee_alias = payload.get("ivitee_alias")
    if isinstance(invitee_id, int):
        return AddMember(access_token, conference_request, invitee_id)
    elif isinstance(invitee_alias, str):
        return AddMember(access_token, conference_request, invitee_alias)
    else:
        raise BadRequest(
            "'invitee_id' or 'invitee_alias' missing or has invalid type"
        )


async def member_remove_params(request: web.Request) -> RemoveMember:
    access_token = get_access_token(request)
    member_request = await member_request_params(request)
    return RemoveMember(access_token, member_request)


async def member_permissions_request_params(
    request: web.Request
) -> GetMemberPermissions:
    access_token = get_access_token(request)
    member_request = await member_request_params(request)
    return GetMemberPermissions(access_token, member_request)


async def member_permissions_edit_params(
    request: web.Request
) -> EditMemberPermissions:
    access_token = get_access_token(request)
    member_request = await member_request_params(request)
    payload = await get_request_payload(request)
    permissions_patch = get_permissions_patch(payload)
    return EditMemberPermissions(
        access_token, member_request, permissions_patch
    )
