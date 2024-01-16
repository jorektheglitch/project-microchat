from itertools import chain
from typing import Any, TypeGuard

from aiohttp import web

from microchat import api
from microchat.api.entities import GetSelf, GetEntity, EditSelf, EditEntity
from microchat.api.entities import RemoveSelf, RemoveEntity
from microchat.api.entities import GetPermissions, EditPermissions
from microchat.api.entities import GetAvatars, GetAvatar, SetAvatar, RemoveAvatar
from microchat.api_utils.exceptions import BadRequest
from microchat.app.route import Route, APIRoute, HTTPMethod, InternalHandler

from .misc import get_disposition, get_permissions_patch
from .misc import int_param, get_request_payload
from .misc import get_access_token


async def self_request_params(request: web.Request) -> GetSelf:
    access_token = get_access_token(request)
    return GetSelf(access_token)


async def self_edit_params(request: web.Request) -> EditSelf:
    access_token = get_access_token(request)
    payload = await get_request_payload(request)
    if not is_str_str_dict(payload):
        raise BadRequest("All given parameters must be strings")
    alias: str | None = payload.get("alias")
    name: str | None = payload.get("name")
    surname: str | None = payload.get("surname")
    bio: str | None = payload.get("bio")
    avatar: str | None = payload.get("avatar")
    return EditSelf(access_token, alias, name, surname, bio, avatar)


async def self_remove_params(request: web.Request) -> RemoveSelf:
    access_token = get_access_token(request)
    return RemoveSelf(access_token)


async def entity_request_params(request: web.Request) -> GetEntity:
    access_token = get_access_token(request)
    entity_id_repr = request.match_info.get("entity_id")
    entity_alias = request.match_info.get("entity_alias")
    if entity_id_repr:
        entity_id = int_param(entity_id_repr)
        return GetEntity(access_token, entity_id)
    elif entity_alias:
        return GetEntity(access_token, entity_alias)
    else:
        raise BadRequest


async def entity_edit_params(request: web.Request) -> EditEntity:
    access_token = get_access_token(request)
    entity_request = await entity_request_params(request)
    payload = await get_request_payload(request)
    if not is_str_str_dict(payload):
        raise BadRequest("All given parameters must be strings")
    return EditEntity(access_token, entity_request, payload)


async def entity_remove_params(request: web.Request) -> RemoveEntity:
    access_token = get_access_token(request)
    entity_request = await entity_request_params(request)
    return RemoveEntity(access_token, entity_request)


async def avatars_request_params(request: web.Request) -> GetAvatars:
    access_token = get_access_token(request)
    entity_request = await entity_request_params(request)
    disposition = get_disposition(request)
    return GetAvatars(access_token, entity_request, disposition)


async def avatar_request_params(request: web.Request) -> GetAvatar:
    access_token = get_access_token(request)
    entity_request = await entity_request_params(request)
    avatar_id_repr = request.match_info.get("avatar_id", "")
    avatar_id = int_param(avatar_id_repr)
    return GetAvatar(access_token, entity_request, avatar_id)


async def avatar_set_params(request: web.Request) -> SetAvatar:
    access_token = get_access_token(request)
    entity_request = await entity_request_params(request)
    payload = await get_request_payload(request)
    avatar_hash = payload.get("avatar")
    if not isinstance(avatar_hash, str):
        raise BadRequest("'avatar' paramter value must be string")
    return SetAvatar(access_token, entity_request, avatar_hash)


async def avatar_delete_params(request: web.Request) -> RemoveAvatar:
    access_token = get_access_token(request)
    entity_request = await entity_request_params(request)
    avatar_no_repr = request.match_info.get("avatar_no", "")
    avatar_no = int_param(avatar_no_repr)
    return RemoveAvatar(access_token, entity_request, avatar_no)


async def permissions_request_params(request: web.Request) -> GetPermissions:
    access_token = get_access_token(request)
    entity_request = await entity_request_params(request)
    return GetPermissions(access_token, entity_request)


async def permissions_edit_params(request: web.Request) -> EditPermissions:
    access_token = get_access_token(request)
    entity_request = await entity_request_params(request)
    payload = await get_request_payload(request)
    permissions_patch = get_permissions_patch(payload)
    return EditPermissions(access_token, entity_request, permissions_patch)


def is_str_str_dict(d: dict[str, Any]) -> TypeGuard[dict[str, str]]:  # type: ignore  # noqa
    return all(isinstance(value, str) for value in d.values())


entity_routes: list[list[APIRoute[Any]]] = [[
    Route(path, HTTPMethod.GET,
          InternalHandler(api.entities.get_entity, entity_request_params)),
    Route(path, HTTPMethod.PATCH,
          InternalHandler(api.entities.edit_entity, entity_edit_params)),
    Route(path, HTTPMethod.DELETE,
          InternalHandler(api.entities.remove_entity, entity_remove_params)),
    Route(fr"{path}/avatars", HTTPMethod.GET,
          InternalHandler(api.entities.list_entity_avatars, avatars_request_params)),
    Route(fr"{path}/avatars", HTTPMethod.POST,
          InternalHandler(api.entities.set_entity_avatar, avatar_set_params)),
    Route(fr"{path}/avatars/{{id:\d+}}", HTTPMethod.GET,
          InternalHandler(api.entities.get_entity_avatar, avatar_request_params)),
    Route(fr"{path}/avatars/{{id:\d+}}", HTTPMethod.DELETE,
          InternalHandler(api.entities.remove_entity_avatar, avatar_delete_params)),
    Route(fr"{path}/permissions", HTTPMethod.GET,
          InternalHandler(api.entities.get_entity_permissions, permissions_request_params)),
    Route(fr"{path}/permissions", HTTPMethod.PATCH,
          InternalHandler(api.entities.edit_entity_permissions, permissions_edit_params)),
    ]
    for path in (r"/entities/{entity_id:\d+}", r"/entities/@{alias:\w+}")
]
routes: list[APIRoute[Any]] = [
    Route("/entities/self", HTTPMethod.GET,
          InternalHandler(api.entities.get_self, self_request_params)),
    Route("/entities/self", HTTPMethod.PATCH,
          InternalHandler(api.entities.edit_self, self_edit_params)),
    Route("/entities/self", HTTPMethod.DELETE,
          InternalHandler(api.entities.remove_self, self_remove_params)),
    *chain.from_iterable(entity_routes)
]
