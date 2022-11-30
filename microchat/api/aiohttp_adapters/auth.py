from dataclasses import dataclass

from aiohttp import web
from microchat.api_utils.exceptions import BadRequest

from microchat.api_utils.request import APIRequest
from .misc import Disposition, get_disposition
from .misc import get_request_payload


@dataclass
class AuthAPIRequest(APIRequest):
    pass


@dataclass
class GetSessions(AuthAPIRequest):
    disposition: Disposition


@dataclass
class AddSession(AuthAPIRequest):
    usename: str
    password: str


@dataclass
class CloseSession(AuthAPIRequest):
    pass


async def sessions_request_params(request: web.Request) -> GetSessions:
    disposition = get_disposition(request)
    return GetSessions(disposition)


async def session_add_params(request: web.Request) -> AddSession:
    payload = await get_request_payload(request)
    username = payload.get("username")
    password = payload.get("password")
    if not isinstance(username, str):
        raise BadRequest("Parameter 'username' must be string")
    if not isinstance(password, str):
        raise BadRequest("Parameter 'password' must be a string")
    return AddSession(username, password)


async def session_close_params(request: web.Request) -> CloseSession:
    return CloseSession()
