from aiohttp import web

from microchat.services import ServiceSet
from microchat.core.entities import ConferenceParticipation, Image, User

from microchat.api_utils import APIResponse, HTTPStatus, api_handler
from microchat.api_utils import BadRequest

from .misc import get_chat, get_entity, get_offset_count


router = web.RouteTableDef()


@router.get("/self")
@api_handler
async def get_self(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    return APIResponse(user)


@router.patch("/self")
@api_handler
async def edit_self(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    overlays: dict[str, str] = {}
    for name, value in payload.items():
        if name not in ("alias", "avatar", "name", "surname", "bio"):
            raise BadRequest(f"Unknown attribute '{name}'")
        if not isinstance(value, str):
            raise BadRequest(
                f"Incorrect value for '{name}'. Values must be string."
            )
        overlays[name] = value
    updated = await services.agents.edit_self(user, **overlays)
    return APIResponse(updated)


@router.delete("/self")
@api_handler
async def remove_self(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    await services.agents.remove_agent(user, user)
    return APIResponse(status=HTTPStatus.NO_CONTENT)


@router.get(r"/{entity_id:\d+}")
@router.get(r"/@{alias:\w+}")
@api_handler
async def get_entity_info(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    entity = await get_entity(services, user, entity_id, alias)
    return APIResponse(entity)


@router.patch(r"/{entity_id:\d+}")
@router.patch(r"/@{alias:\w+}")
@api_handler
async def edit_entity(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    entity = await get_entity(services, user, entity_id, alias)
    overlays: dict[str, str] = {}
    for name, value in payload.items():
        if not isinstance(value, str):
            raise BadRequest(
                f"Incorrect value for '{name}'. Values must be string."
            )
        overlays[name] = value
    updated = await services.agents.edit_agent(user, entity, **overlays)
    return APIResponse(updated)


@router.get(r"/{entity_id:\d+}")
@api_handler
async def remove_entity(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    entity = await get_entity(services, user, entity_id, alias)
    await services.agents.remove_agent(user, entity)
    return APIResponse(status=HTTPStatus.NO_CONTENT)


@router.get(r"/{entity_id:\d+}/avatars")
@router.get(r"/@{alias:\w+}/avatars")
@api_handler
async def list_entity_avatars(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    entity = await get_entity(services, user, entity_id, alias)
    offset, count = get_offset_count(request)
    avatars = await services.agents.list_avatars(
        user, entity, offset, count
    )
    return APIResponse(avatars)


@router.get(r"/{entity_id:\d+}/avatars/{id:\d+}")
@router.get(r"/@{alias:\w+}/avatars/{id:\d+}")
@api_handler
async def get_entity_avatar(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    entity = await get_entity(services, user, entity_id, alias)
    avatar_index_raw = request.match_info.get("id", -1)
    try:
        avatar_index = int(avatar_index_raw)
    except (ValueError, TypeError):
        raise BadRequest("Invalid `offset` or `count` params")
    avatars = await services.agents.get_avatar(
        user, entity, avatar_index
    )
    return APIResponse(avatars)


@router.post(r"/@{alias:\w+}/avatars")
@api_handler
async def set_entity_avatar(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    if not alias:
        raise BadRequest("Empty username")
    image_hash = payload.get("image")
    if not image_hash:
        raise BadRequest("Missing 'image' parameter")
    entity = await get_entity(services, user, entity_id, alias)
    avatar = await services.files.get_info(user, image_hash)
    if not isinstance(avatar, Image):
        raise BadRequest("Given id does not refers to image")
    await services.agents.set_avatar(user, entity, avatar)
    return APIResponse(avatar)


@router.delete(r"/@{alias:\w+}/avatars/{id:\d+}")
@api_handler
async def remove_entity_avatar(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    id = request.match_info.get("id", -1)
    avatar_id = int(id)
    if not alias:
        raise BadRequest("Empty username or avatar id")
    entity = await get_entity(services, user, entity_id, alias)
    await services.agents.remove_avatar(user, entity, avatar_id)
    return APIResponse(status=HTTPStatus.NO_CONTENT)


@router.get(r"/{entity_id:\d+}/permissions")
@router.get(r"/@{alias:\w+}/permissions")
@api_handler
async def get_entity_permissions(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    relation = await get_chat(services, user, entity_id, alias)
    if isinstance(relation, ConferenceParticipation):
        raise BadRequest("Can't ask for conference's permissions")
    return APIResponse(relation.permissions)


@router.patch(r"/{entity_id:\d+}/permissions")
@router.patch(r"/@{alias:\w+}/permissions")
@api_handler
async def edit_entity_permissions(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    entity_id = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    relation = await get_chat(services, user, entity_id, alias)
    if isinstance(relation, ConferenceParticipation):
        raise BadRequest("Can't manage conference's permissions")
    overlay: dict[str, bool] = {}
    await services.agents.edit_permissions(user, relation, **overlay)
    return APIResponse(relation.permissions)
