from typing import Literal, TypeGuard
from typing import cast

from aiohttp import web

from microchat.api_utils.exceptions import BadRequest


def media_add_params(request: web.Request):
    pass


def get_offset_count(
    request: web.Request, defaults: tuple[int, int] = (0, 100)
) -> tuple[int, int]:
    default_offset, default_count = defaults
    offset = request.query.get("offset", default_offset)
    count = request.query.get("count", default_count)
    try:
        offset = int(offset)
        count = int(count)
    except (ValueError, TypeError):
        raise BadRequest("Invalid 'offset' or 'count' params")
    return offset, count


def chat_view_params(
    request: web.Request
) -> tuple[int, None] | tuple[None, str]:
    entity_id_repr = request.match_info.get("entity_id")
    alias = request.match_info.get("alias")
    if entity_id_repr:
        return int(entity_id_repr), None
    elif alias:
        return None, alias
    else:
        raise BadRequest


def message_view_params(
    request: web.Request
) -> tuple[int | None, str | None, int]:
    entity_id, alias = chat_view_params(request)
    try:
        message_id_repr = request.match_info["message_id"]
        message_id = int(message_id_repr)
    except (KeyError, ValueError):
        raise BadRequest
    return entity_id, alias, message_id


def content_view_params(
    request: web.Request
) -> tuple[int | None, str | None, int, int, Literal['content', 'preview']]:
    entity_id, alias, message_id = message_view_params(request)
    try:
        attachment_id = int(request.match_info["id"])
        view_kind = request.match_info["view"]
        view_kind = cast(Literal["content", "preview"], view_kind)
    except (KeyError, ValueError):
        raise BadRequest
    if not check_view_kind(view_kind):
        raise BadRequest
    return entity_id, alias, message_id, attachment_id, view_kind


def check_view_kind(
    view_kind: str
) -> TypeGuard[Literal["content", "preview"]]:
    return view_kind in ("content", "preview")
