from dataclasses import dataclass


@dataclass
class APIRequest:
    pass


@dataclass
class AuthenticatedRequest(APIRequest):
    access_token: str


@dataclass
class CookieAuthenticatedRequest(AuthenticatedRequest):
    access_token: str  # cookie
    csrf_token: str  # query parameter
