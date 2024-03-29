from typing import Any, cast

from aiohttp import web

from microchat.api.misc import Disposition, PermissionsPatch
from microchat.core.entities import PERMISSIONS_FIELDS
from microchat.api_utils.exceptions import BadRequest, Unauthorized


def int_param(string: str, name: str | None = None) -> int:
    try:
        return int(string)
    except ValueError:
        if name:
            raise BadRequest(f"'{name}' parameter must be int")
        else:
            raise BadRequest


def get_access_token(request: web.Request) -> str:
    auth_header = request.headers.get("Authentication")
    if auth_header is None:
        raise Unauthorized("Missing 'Authentication' header")
    if not auth_header.startswith("Bearer "):
        raise Unauthorized(
            "Incorrect 'Authentication' header value. "
            "Make sure that value matches pattern 'Bearer {token}'."
        )
    _, token = auth_header.split(" ", maxsplit=1)
    return token


def get_media_access_info(request: web.Request) -> tuple[str, str]:
    auth_cookie = request.cookies.get("MEDIA_ACCESS_TOKEN")
    csrf_token = request.query.get("csrf_token")
    if not auth_cookie:
        raise Unauthorized("Missing 'MEDIA_ACCESS_TOKEN' cookie")
    if not csrf_token:
        raise Unauthorized("Missing csrf_token URL paraneter")
    return auth_cookie, csrf_token


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


def get_permissions_patch(params: dict[str, Any]) -> PermissionsPatch:  # type: ignore  # noqa
    patch = {key: params.get(key) for key in PERMISSIONS_FIELDS}
    if not all(isinstance(value, bool) for value in patch.values()):
        raise BadRequest("All parameters must be booleans")
    return cast(PermissionsPatch, patch)
