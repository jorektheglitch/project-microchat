from aiohttp import web

from microchat.api_utils.exceptions import BadRequest
from microchat.api.auth_ import GetSessions, AddSession, CloseSession

from .misc import get_disposition
from .misc import get_request_payload


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
