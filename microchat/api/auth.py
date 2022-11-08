from aiohttp import web

from microchat.services import ServiceSet, AccessToken
from microchat.core.entities import User

from microchat.api_utils import AccessLevel, api_handler, APIResponse
from microchat.api_utils import BadRequest


router = web.RouteTableDef()


@router.get("/sessions")
@api_handler
async def list_sessions(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise BadRequest("Invalid body")
    offset = payload.get("offset", 0)
    count = payload.get("count", 10)
    if not (isinstance(offset, int) or isinstance(count, int)):
        raise BadRequest("Invalid body")
    sessions = await services.auth.list_sessions(user, offset, count)
    return APIResponse(sessions)


@router.post("/sessions")
@api_handler(AccessLevel.ANY)
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


@router.delete(r"/sessions/{token:\w+}")
@api_handler
async def terminate_session(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    token_raw = request.match_info.get("token")
    if not token_raw:
        raise BadRequest("Invalid or missing token")
    token = AccessToken(token_raw)
    session = await services.auth.resolve_token(token)
    if user == session.auth.user:
        await services.auth.terminate_session(user, session)
    else:
        raise BadRequest("Invalid or missing token")
    return APIResponse()
