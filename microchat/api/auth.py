from dataclasses import dataclass

from microchat.api_utils.request import APIRequest, AuthenticatedRequest
from microchat.api_utils.response import APIResponse, Status
from microchat.api_utils.handler import authenticated
from microchat.core.entities import Session, User
from microchat.services import ServiceSet

from .misc import Disposition


@dataclass
class AuthAPIRequest(APIRequest):
    pass


@dataclass
class GetSessions(AuthAPIRequest, AuthenticatedRequest):
    disposition: Disposition


@dataclass
class AddSession(AuthAPIRequest):
    username: str
    password: str


@dataclass
class CloseSession(AuthAPIRequest, AuthenticatedRequest):
    id: int | None


async def add_session(
    request: AddSession, services: ServiceSet
) -> APIResponse[str]:
    username = request.username
    password = request.password
    access_token = await services.auth.new_session(username, password)
    return APIResponse(access_token, status=Status.CREATED)


@authenticated
async def list_sessions(
    request: GetSessions, services: ServiceSet, user: User
) -> APIResponse[list[Session]]:
    offset = request.disposition.offset
    count = request.disposition.count
    sessions = await services.auth.list_sessions(user, offset, count)
    return APIResponse(sessions)


@authenticated
async def terminate_session(
    request: CloseSession, services: ServiceSet, user: User
) -> APIResponse[None]:
    session_id = request.id
    if session_id is not None:
        session = await services.auth.get_session(user, session_id)
    await services.auth.terminate_session(user, session)
    return APIResponse(status=Status.NO_CONTENT)
