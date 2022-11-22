from dataclasses import dataclass

from typing import Any, TypedDict, cast

from aiohttp import web

from microchat.core.entities import PERMISSIONS_FIELDS
from microchat.api_utils.exceptions import BadRequest


@dataclass
class Disposition:
    offset: int | None
    count: int | None


class PermissionsPatch(TypedDict):
    read: bool | None
    send: bool | None
    delete: bool | None
    send_media: bool | None
    send_mediamessage: bool | None
    add_user: bool | None
    pin_message: bool | None
    edit_conference: bool | None


def int_param(string: str, name: str | None = None) -> int:
    try:
        return int(string)
    except ValueError:
        if name:
            raise BadRequest(f"'{name}' parameter must be int")
        else:
            raise BadRequest


def get_disposition(request: web.Request) -> Disposition:
    offset, count = None, None
    offset_repr = request.query.get("offset")
    count_repr = request.query.get("count")
    if offset_repr is not None:
        offset = int_param(offset_repr, "offset")
    if count_repr is not None:
        count = int_param(count_repr, "count")
    return Disposition(offset, count)


async def get_request_payload(  # type: ignore
    request: web.Request
) -> dict[str, Any]:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Request body must be dict")
    if not all(isinstance(key, str) for key in payload):
        raise BadRequest("All keys from body must be strings")
    return payload


def get_permissions_patch(params: dict[str, Any]) -> PermissionsPatch:  # type: ignore
    patch = {key: params.get(key) for key in PERMISSIONS_FIELDS}
    if not all(isinstance(value, bool) for value in patch.values()):
        raise BadRequest("All parameters must be booleans")
    return cast(PermissionsPatch, patch)
