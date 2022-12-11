from dataclasses import dataclass


@dataclass
class APIRequest:
    pass


@dataclass
class Authenticated:
    access_token: str


@dataclass
class CookieAuthenticated(Authenticated):
    access_token: str
    csrf_token: str
