from typing import TypedDict
from typing import cast

import jwt


class SessionInfo(TypedDict):
    session: int
    user: int


class IncompleteJWT(Exception):
    pass


class JWTManager:
    secret: str

    def __init__(self, secret: str) -> None:
        self.secret = secret

    def decode_access_token(self, token: str) -> SessionInfo:
        return cast(SessionInfo, jwt.decode(token, self.secret))

    def decode_csrf_token(self, token: str) -> SessionInfo:
        return cast(SessionInfo, jwt.decode(token, self.secret))

    def create_access_token(self, user_id: int, session_id: int) -> str:
        session_info = dict(session=session_id, user=user_id)
        return jwt.encode(session_info, self.secret)
