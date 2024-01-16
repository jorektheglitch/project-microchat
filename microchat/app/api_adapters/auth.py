from typing import Any, Sequence
from aiohttp import web

from microchat import api
from microchat.api.auth import GetSessions, AddSession, CloseSession
from microchat.api_utils.exceptions import BadRequest
from microchat.api_utils.response import APIResponse
from microchat.app.route import Route, HTTPMethod, InternalHandler
from microchat.core.entities import Entity
from microchat.services import ServiceSet

from .misc import get_access_token, get_disposition
from .misc import get_request_payload


async def sessions_request_params(request: web.Request) -> GetSessions:
    access_token = get_access_token(request)
    disposition = get_disposition(request)
    return GetSessions(access_token, disposition)


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
    access_token = get_access_token(request)
    session_id_repr = request.match_info.get("session_id")
    session_id: int | None = None
    if session_id_repr is not None:
        session_id = int(session_id_repr)
    return CloseSession(access_token, id=session_id)


routes: list[Route[Any, ServiceSet, APIResponse[str | None | Entity | Sequence[Entity]]]] = [
    Route(
        "/auth/sessions", HTTPMethod.POST,
        InternalHandler(api.auth.add_session, session_add_params)
    ),
    Route(
        "/auth/sessions", HTTPMethod.GET,
        InternalHandler(api.auth.list_sessions, sessions_request_params)
    ),
    Route(
        r"/auth/sessions/{session_id:\w+}", HTTPMethod.DELETE,
        InternalHandler(api.auth.terminate_session, session_close_params)
    ),
]
