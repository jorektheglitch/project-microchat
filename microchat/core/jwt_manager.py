from typing import Any

import jwt


class JWTManager:
    secret: str

    def __init__(self, secret: str) -> None:
        self.secret = secret

    def decode(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, self.secret)

    def encode(self, payload: dict[str, Any]) -> str:
        return jwt.encode(payload, self.secret)
