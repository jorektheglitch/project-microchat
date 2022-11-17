from aiohttp import web

from microchat.services import ServiceSet
from microchat.core.entities import User

from microchat.api_utils import AccessLevel, api_handler, APIResponse
from microchat.api_utils import BadRequest


router = web.RouteTableDef()


@router.get("/sessions")
@api_handler
async def list_sessions(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    offset = request.query.get("offset", 0)
    count = request.query.get("count", 10)
    try:
        offset = int(offset)
        count = int(count)
    except (ValueError, TypeError):
        raise BadRequest("Invalid offset or count params")
    sessions = await services.auth.list_sessions(user, offset, count)
    return APIResponse(sessions)


@router.post("/sessions")
@api_handler(access_level=AccessLevel.ANY)
async def get_access_token(
    request: web.Request, services: ServiceSet
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    username: str | None = payload.get("username")
    password: str | None = payload.get("password")
    if not (username and password):
        raise BadRequest("Missing username or password")
    access_token = await services.auth.new_session(username, password)
    return APIResponse(access_token)


@router.delete(r"/sessions/{session_id:\w+}")
@api_handler
async def terminate_session(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    id_raw = request.match_info.get("session_id")
    if not id_raw:
        raise BadRequest("Invalid or missing session_id")
    try:
        session_id = int(id_raw)
    except (TypeError, ValueError):
        raise BadRequest("Incorrect 'session_id' parameter")
    session = await services.auth.get_session(user, session_id)
    if user == session.auth.user:
        await services.auth.terminate_session(user, session)
    else:
        raise BadRequest("Invalid or missing token")
    return APIResponse()
