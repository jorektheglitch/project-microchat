from dataclasses import dataclass

from typing import TypedDict

from aiohttp import web

from microchat.core.entities import User
from microchat.services import ServiceSet, AuthenticationError


@dataclass
class Disposition:
    offset: int
    count: int


class PermissionsPatch(TypedDict):
    read: bool | None
    send: bool | None
    delete: bool | None
    send_media: bool | None
    send_mediamessage: bool | None
    add_user: bool | None
    pin_message: bool | None
    edit_conference: bool | None


async def authenticate_media_request(
    request: web.Request, services: ServiceSet
) -> User:
    try:
        auth_cookie = request.cookies["MEDIA_ACCESS"]
        csrf_token = request.query["csrf_token"]
    except KeyError:
        raise AuthenticationError
    session = await services.auth.resolve_media_token(
        auth_cookie, csrf_token
    )
    user = session.auth.user
    return user
