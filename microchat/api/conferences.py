from aiohttp import web

from microchat.services import ServiceSet
from microchat.core.entities import Bot, User, Conference
from microchat.core.entities import PERMISSIONS_FIELDS

from microchat.api_utils import APIResponse, HTTPStatus, api_handler
from microchat.api_utils import BadRequest, NotFound


router = web.RouteTableDef()


@router.get(r"/@{alias:\w+}/members")
@api_handler
async def list_chat_members(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    alias = request.match_info.get("alias")
    if not alias:
        raise BadRequest("Empty username")
    offset = request.query.get("offset", 0)
    count = request.query.get("count", 10)
    try:
        offset = int(offset)
        count = int(count)
    except (ValueError, TypeError):
        raise BadRequest("Invalid offset or count params")
    if not (isinstance(offset, int) and isinstance(count, int)):
        raise BadRequest("Invalid parameters")
    conference = await services.agents.resolve_alias(user, alias)
    if not isinstance(conference, Conference):
        raise NotFound
    members = await services.conferences.list_chat_members(
        user, conference, offset, count
    )
    return APIResponse(members)


@router.post(r"/@{alias:\w+}/members")
@api_handler
async def add_chat_member(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    alias = request.match_info.get("alias")
    if not alias:
        raise BadRequest("Empty username")
    username = payload.get("username")
    user_id_repr = payload.get("user_id")
    if isinstance(username, str):
        invitee = await services.agents.resolve_alias(user, username)
    elif isinstance(user_id_repr, str):
        try:
            user_id = int(user_id_repr)
        except (ValueError, TypeError):
            raise BadRequest("Invalid agent id")
        else:
            invitee = await services.agents.get(user, user_id)
    else:
        raise BadRequest("Missing username or user_id parameter")
    if isinstance(invitee, Conference):
        raise BadRequest("Invalid agent id or username")
    conference = await services.agents.resolve_alias(user, alias)
    if not isinstance(conference, Conference):
        raise NotFound
    member = await services.conferences.add_chat_member(
        user, conference, invitee
    )
    return APIResponse(member, HTTPStatus.CREATED)


@router.get(r"/@{alias:\w+}/members/{id:\d+}")
@router.get(r"/@{alias:\w+}/members/{member_alias:\w+}")
@api_handler
async def get_chat_member(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    alias = request.match_info.get("alias")
    id_repr = request.match_info.get("id")
    member_alias = request.match_info.get("member_alias")
    if not alias:
        raise BadRequest("Empty username")
    if isinstance(member_alias, str):
        agent = await services.agents.resolve_alias(user, member_alias)
    elif isinstance(id_repr, str):
        try:
            agent_id = int(id_repr)
        except (ValueError, TypeError):
            raise BadRequest("Invalid agent id")
        else:
            agent = await services.agents.get(user, agent_id)
    else:
        raise BadRequest("Missing username or user_id parameter")
    if not isinstance(agent, (User, Bot)):
        raise BadRequest("Agent id/alias must refers to User or Bot")
    conference = await services.agents.resolve_alias(user, alias)
    if not isinstance(conference, Conference):
        raise NotFound
    member = await services.conferences.get_chat_member(
        user, conference, agent
    )
    return APIResponse(member)


@router.delete(r"/@{alias:\w+}/members/{id:\d+}")
@router.delete(r"/@{alias:\w+}/members/{member_alias:\w+}")
@api_handler
async def remove_chat_member(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    alias = request.match_info.get("alias")
    id_repr = request.match_info.get("id")
    member_alias = request.match_info.get("member_alias")
    if not alias:
        raise BadRequest("Empty username")
    if isinstance(member_alias, str):
        agent = await services.agents.resolve_alias(user, member_alias)
    elif isinstance(id_repr, str):
        try:
            agent_id = int(id_repr)
        except (ValueError, TypeError):
            raise BadRequest("Invalid agent id")
        else:
            agent = await services.agents.get(user, agent_id)
    else:
        raise BadRequest("Missing username or user_id parameter")
    if not isinstance(agent, (User, Bot)):
        raise BadRequest("Agent id/alias must refers to User or Bot")
    conference = await services.agents.resolve_alias(user, alias)
    if not isinstance(conference, Conference):
        raise NotFound
    await services.conferences.get_chat_member(
        user, conference, agent
    )
    return APIResponse(status=HTTPStatus.NO_CONTENT)


@router.get(r"/@{alias:\w+}/members/{id:\d+}/permissions")
@router.get(r"/@{alias:\w+}/members/{member_alias:\w+}/permissions")
@api_handler
async def get_chat_member_permissions(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    alias = request.match_info.get("alias")
    id_repr = request.match_info.get("id")
    member_alias = request.match_info.get("member_alias")
    if not alias:
        raise BadRequest("Empty username")
    if isinstance(member_alias, str):
        agent = await services.agents.resolve_alias(user, member_alias)
    elif isinstance(id_repr, str):
        try:
            agent_id = int(id_repr)
        except (ValueError, TypeError):
            raise BadRequest("Invalid agent id")
        else:
            agent = await services.agents.get(user, agent_id)
    else:
        raise BadRequest("Missing username or user_id parameter")
    if not isinstance(agent, (User, Bot)):
        raise BadRequest("Agent id/alias must refers to User or Bot")
    conference = await services.agents.resolve_alias(user, alias)
    if not isinstance(conference, Conference):
        raise NotFound
    permissions = await services.conferences.get_chat_member_permissions(
        user, conference, agent
    )
    return APIResponse(permissions)


@router.patch(r"/@{alias:\w+}/members/{id:\d+}/permissions")
@router.patch(r"/@{alias:\w+}/members/{member_alias:\w+}/permissions")
@api_handler
async def edit_chat_member_permissions(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    alias = request.match_info.get("alias")
    id_repr = request.match_info.get("id")
    member_alias = request.match_info.get("member_alias")
    if not alias:
        raise BadRequest("Empty username")
    if isinstance(member_alias, str):
        agent = await services.agents.resolve_alias(user, member_alias)
    elif isinstance(id_repr, str):
        try:
            agent_id = int(id_repr)
        except (ValueError, TypeError):
            raise BadRequest("Invalid agent id")
        else:
            agent = await services.agents.get(user, agent_id)
    else:
        raise BadRequest("Missing username or user_id parameter")
    if not isinstance(agent, (User, Bot)):
        raise BadRequest("Agent id/alias must refers to User or Bot")
    conference = await services.agents.resolve_alias(user, alias)
    if not isinstance(conference, Conference):
        raise NotFound
    overalys: dict[str, bool] = {}
    for name, value in payload.items():
        if name not in PERMISSIONS_FIELDS:
            raise BadRequest(f"Unknown permission '{name}'")
        if not isinstance(value, bool):
            raise BadRequest(
                f"Incorrect value for '{name}'. Values must be bool."
            )
        overalys[name] = value
    permissions = await services.conferences.edit_chat_member_permissions(
        user, conference, agent, **overalys
    )
    return APIResponse(permissions)
