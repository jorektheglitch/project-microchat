from __future__ import annotations

from microchat.core.entities import User, Session
from microchat.core.jwt_manager import JWTManager
from microchat.storages import UoW

from .base_service import Service
from .general_exceptions import ServiceError


class AuthenticationError(ServiceError):
    pass


class InvalidCredentials(AuthenticationError):
    pass


class UnsupportedMethod(AuthenticationError):
    pass


class MissingToken(AuthenticationError):
    pass


class InvalidToken(AuthenticationError):
    pass


class Auth(Service):
    jwt_manager: JWTManager

    def __init__(self, uow: UoW, jwt_manager: JWTManager) -> None:
        super().__init__(uow)
        self.jwt_manager = jwt_manager

    async def new_session(self, username: str, password: str) -> str:
        entity = await self.uow.entities.get_by_alias(username)
        if not isinstance(entity, User):
            raise InvalidCredentials()
        auth_info = await self.uow.auth.get_auth_data(entity, "password")
        try:
            auth_succeed = auth_info.check(password.encode())
        except NotImplementedError as e:
            raise UnsupportedMethod(e.args[0])
        if not auth_succeed:
            raise InvalidCredentials()
        session = await self.uow.auth.create_session(entity, auth_info)
        token = self.jwt_manager.create_access_token(entity.id, session.id)
        return token

    async def list_sessions(
        self, user: User, offset: int, count: int
    ) -> list[Session]:
        return list(await user.sessions[offset:offset+count])

    async def get_session(self, user: User, id: int) -> Session:
        session = await user.sessions[id]
        return session

    async def resolve_token(self, token: str) -> Session:
        payload = self.jwt_manager.decode_access_token(token)
        entity = await self.uow.entities.get_by_id(payload["user"])
        if not isinstance(entity, User):
            raise InvalidToken()
        session = await entity.sessions[payload["session"]]
        return session

    async def resolve_media_token(
        self, media_cookie: str, csrf_token: str
    ) -> Session:
        session_info = self.jwt_manager.decode_access_token(media_cookie)
        csrf_info = self.jwt_manager.decode_csrf_token(csrf_token)
        # TODO: add CSRF token checking
        entity = self.uow.entities.get_by_id(session_info["user"])
        if not isinstance(entity, User):
            raise InvalidToken()
        session = await entity.sessions[session_info["session"]]
        return session

    async def terminate_session(self, user: User, session: Session) -> None:
        await self.uow.auth.terminate_session(user, session)
