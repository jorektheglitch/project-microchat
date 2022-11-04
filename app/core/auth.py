from functools import wraps
from typing import Callable, Optional

from aiohttp.web import Request, Response, middleware
from aiohttp.web import HTTPForbidden, HTTPBadRequest

from app.models import Token
from app.core.entities import User


BANNER = "Only for authorized users"


class AuthenticationReqired(Exception): ...  # noqa


def get_token(request: Request) -> Optional[str]:
    """
    Extracts auth token from request.
    """
    token = None
    auth_cookie = request.cookies.get('Authorization')
    auth_header = request.headers.get('Authorization')
    if auth_cookie:
        token = auth_cookie
    if auth_header:
        auth_type, raw_token = auth_header.split(maxsplit=1)
        if auth_type == 'Bearer':
            token = raw_token
    return token


async def get_user(request: Request) -> Optional[User]:
    """
    """

    raw_token = get_token(request)
    if raw_token is None:
        return None
    token = bytes.fromhex(raw_token)
    user_obj = await Token.get_user(token)
    if user_obj is None:
        return None
    user = User.from_object(user_obj)
    return user


@middleware
async def auth_middleware(request: Request, handler) -> Response:
    try:
        user = await get_user(request)
    except Exception:
        raise HTTPForbidden(
            reason="InvalidToken",
            body=BANNER.encode()
        )
    request['user'] = user
    request['user_id'] = user.id
    return await handler(request)


def auth_required(handler) -> Callable:
    """
    """

    banner = BANNER.encode()

    @wraps(handler)
    async def wrapped(request: Request) -> Response:
        try:
            user = await get_user(request)
        except Exception:
            raise HTTPForbidden(
                # reason="",
                body=banner
            )
        if user is None:
            raise HTTPForbidden(
                # reason="",
                body=banner
            )
        request['user'] = user
        request['user_id'] = user.id
        return await handler(request)

    return wrapped


def sse_auth_required(handler):
    """
    """

    banner = BANNER.encode()

    @wraps(handler)
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
