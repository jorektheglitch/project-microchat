from __future__ import annotations

from abc import ABC

from typing import ClassVar

from microchat.services import ServiceError

from .response import APIResponse, JSON


class APIError(ABC, Exception, APIResponse[JSON]):
    status_code: ClassVar[int]

    def __init__(
        self,
        msg: str | None = None,
        *,
        payload: JSON = None,
        reason: str | None = None
    ) -> None:
        super().__init__(msg)
        if payload is None and msg is not None:
            self.payload = msg
        else:
            self.payload = payload
        self.reason = reason

    @classmethod
    def from_service_exc(cls, exc: ServiceError) -> APIError:
        pass


class BadRequest(APIError):
    status_code = 400


class Unauthorized(APIError):
    status_code = 401


class Forbidden(APIError):
    status_code = 403


class NotFound(APIError):
    status_code = 404
