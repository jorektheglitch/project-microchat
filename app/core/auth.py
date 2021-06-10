from typing import Tuple, Callable, Optional

from aiohttp.web import Request, Response, middleware
from aiohttp.web import HTTPForbidden, HTTPBadRequest

from app.models import User, Token


BANNER = "Only for authorized users"


class AuthenticationReqired(Exception): ...  # noqa


async def get_user(request: Request) -> Tuple[Optional[User], Optional[int]]:
    """
    """

    user = None
    user_id = None
    auth_header = request.headers.get('Authorization')
    if auth_header:
        auth_type, hex_token = auth_header.split(maxsplit=1)
        try:
            token = bytes.fromhex(hex_token)
        except ValueError:
            pass
        else:
            if auth_type == 'Bearer':
                user = await Token.get_user(token)
                user_id = getattr(user, 'id', None)

    return user, user_id


async def get_user_by_cookie(request):
    """
    """

    user = None
    user_id = None
    auth_cookie = request.cookies.get('Authorization')
    if auth_cookie:
        try:
            token = bytes.fromhex(auth_cookie)
        except ValueError:
            pass
        else:
            user = await Token.get_user(token)
            user = getattr(user, 'id', None)

    return user, user_id


@middleware
async def auth_middleware(request: Request, handler) -> Response:
    user, user_id = await get_user(request)
    if user_id is None:
        raise HTTPForbidden(
            # reason="",
            body=BANNER.encode()
        )
    request['user'] = user
    request['user_id'] = user_id
    return await handler(request)


def auth_required(handler) -> Callable:
    """
    """

    banner = BANNER.encode()

    async def wrapped(request: Request) -> Response:
        user, user_id = await get_user(request)
        if user_id is None:
            user, user_id = await get_user_by_cookie(request)
        if user_id is None:
            raise HTTPForbidden(
                # reason="",
                body=banner
            )
        request['user'] = user
        request['user_id'] = user_id
        return await handler(request)

    return wrapped


def sse_auth_required(handler):
    """
    """

    banner = BANNER.encode()

    async def wrapped(request: Request):
        pseudo = request.clone()
        params = pseudo.query
        hex_token = params.get('access_token')
        user_id = None
        try:
            token = bytes.fromhex(hex_token)
        except (TypeError, ValueError):
            raise HTTPBadRequest(
                # reason="",
                body="invalid token".encode()
            )
        else:
            user_row = await Token.get_user(token)
            user_id = getattr(user_row, 'id', None)
            if user_id:
                request['user'] = user_row
                request['user_id'] = user_id
                return await handler(request)
            raise HTTPBadRequest(
                # reason="",
                body=banner
            )
    return wrapped
