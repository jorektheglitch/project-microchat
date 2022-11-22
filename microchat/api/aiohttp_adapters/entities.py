from dataclasses import dataclass
from typing import Any, TypeGuard

from aiohttp import web
from microchat.api_utils.exceptions import BadRequest

from microchat.api_utils.request import APIRequest
from .misc import Disposition, get_disposition
from .misc import PermissionsPatch, get_permissions_patch
from .misc import int_param, get_request_payload


@dataclass
class GetSelf(APIRequest):
    pass


@dataclass
class EditSelf(APIRequest):
    alias: str | None
    name: str | None
    surname: str | None
    bio: str | None
    avatar: str | None


@dataclass
class RemoveSelf(APIRequest):
    pass


@dataclass
class GetEntity(APIRequest):
    entity: str | int


@dataclass
class EditEntity(APIRequest):
    entity_request: GetEntity
    update: dict[str, str]


@dataclass
class RemoveEntity(APIRequest):
    entity_request: GetEntity


@dataclass
class GetAvatars(APIRequest):
    entity_request: GetEntity
    disposition: Disposition


@dataclass
class GetAvatar(APIRequest):
    entity_request: GetEntity
    avatar_id: int


@dataclass
class SetAvatar(APIRequest):
    entity_request: GetEntity
    avatar: str


@dataclass
class RemoveAvatar(APIRequest):
    avatar_request: GetAvatar


@dataclass
class GetPermissions(APIRequest):
    entity_request: GetEntity


@dataclass
class EditPermissions(APIRequest):
    entity_request: GetEntity
    permissions_patch: PermissionsPatch


async def self_request_params(request: web.Request) -> GetSelf:
    return GetSelf()


async def self_edit_params(request: web.Request) -> EditSelf:
    payload = await get_request_payload(request)
    if not is_str_str_dict(payload):
        raise BadRequest("All given parameters must be strings")
    alias: str | None = payload.get("alias")
    name: str | None = payload.get("name")
    surname: str | None = payload.get("surname")
    bio: str | None = payload.get("bio")
    avatar: str | None = payload.get("avatar")
    return EditSelf(alias, name, surname, bio, avatar)


async def self_remove_params(request: web.Request) -> RemoveSelf:
    return RemoveSelf()


async def entity_request_params(request: web.Request) -> GetEntity:
    entity_id_repr = request.match_info.get("entity_id")
    entity_alias = request.match_info.get("entity_alias")
    if entity_id_repr:
        entity_id = int_param(entity_id_repr)
        return GetEntity(entity_id)
    elif entity_alias:
        return GetEntity(entity_alias)
    else:
        raise BadRequest


async def entity_edit_params(request: web.Request) -> EditEntity:
    entity_request = await entity_request_params(request)
    payload = await get_request_payload(request)
    if not is_str_str_dict(payload):
        raise BadRequest("All given parameters must be strings")
    return EditEntity(entity_request, payload)


async def entity_remove_params(request: web.Request) -> RemoveEntity:
    entity_request = await entity_request_params(request)
    return RemoveEntity(entity_request)


async def avatars_request_params(request: web.Request) -> GetAvatars:
    entity_request = await entity_request_params(request)
    disposition = get_disposition(request)
    return GetAvatars(entity_request, disposition)


async def avatar_request_params(request: web.Request) -> GetAvatar:
    entity_request = await entity_request_params(request)
    avatar_id_repr = request.match_info.get("avatar_id", "")
    avatar_id = int_param(avatar_id_repr)
    return GetAvatar(entity_request, avatar_id)


async def avatar_set_params(request: web.Request) -> SetAvatar:
    entity_request = await entity_request_params(request)
    payload = await get_request_payload(request)
    avatar_hash = payload.get("avatar")
    if not isinstance(avatar_hash, str):
        raise BadRequest("'avatar' paramter value must be string")
    return SetAvatar(entity_request, avatar_hash)


async def avatar_delete_params(request: web.Request) -> RemoveAvatar:
    avatar_request = await avatar_request_params(request)
    return RemoveAvatar(avatar_request)


async def permissions_request_params(request: web.Request) -> GetPermissions:
    entity_request = await entity_request_params(request)
    return GetPermissions(entity_request)


async def permissions_edit_params(request: web.Request) -> EditPermissions:
    entity_request = await entity_request_params(request)
    payload = await get_request_payload(request)
    permissions_patch = get_permissions_patch(payload)
    return EditPermissions(entity_request, permissions_patch)


def is_str_str_dict(d: dict[str, Any]) -> TypeGuard[dict[str, str]]:  # type: ignore  # noqa
    return all(isinstance(value, str) for value in d.values())
