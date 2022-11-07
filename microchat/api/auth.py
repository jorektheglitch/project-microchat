from aiohttp import web

from microchat.services import ServiceSet, AccessToken
from microchat.core.entities import User

from microchat.api_utils import AccessLevel, api_handler, APIResponse


router = web.RouteTableDef()


@router.get("/sessions")
@api_handler
async def list_sessions(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        return web.json_response(
            {"error": "invalid body"},
            status=400
        )
    offset = payload.get("offset", 0)
    count = payload.get("count", 10)
    if not (isinstance(offset, int) or isinstance(count, int)):
        return web.json_response(
            {},
            status=400
        )
    sessions = await services.auth.list_sessions(user, offset, count)
    return web.json_response({
        "response": [
            {
                "name": session.name,
                "location": session.location,
                "ip": session.ip_address,
                "auth": session.auth.method
            } for session in sessions
        ]
    })


@router.post("/sessions")
@api_handler(AccessLevel.ANY)
async def get_access_token(request: web.Request) -> APIResponse:
    payload = await request.json()
    if not isinstance(payload, dict):
        return web.json_response(
            {"error": "invalid body"},
            status=400
        )
    username: str | None = payload.get("username")
    password: str | None = payload.get("password")
    if not (username and password):
        return web.json_response(
            {"error": "missing username or password"},
            status=400
        )
    services: ServiceSet = request["services"]
    access_token = await services.auth.new_session(username, password)
    return web.json_response({"response": {"access_token": access_token}})


@router.delete(r"/sessions/{token:\w+}")
@api_handler
async def terminate_session(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    token_raw = request.match_info.get("token")
    if not token_raw:
        return web.json_response(
            {"error": "invalid or missing token"},
            status=400
        )
    token = AccessToken(token_raw)
    session = await services.auth.resolve_token(token)
    if user == session.auth.user:
        await services.auth.terminate_session(user, session)
    else:
        return web.json_response(
            {"error": "invalid or missing token"},
            status=400
        )
    return web.Response()
