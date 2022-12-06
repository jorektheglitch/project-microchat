from dataclasses import dataclass


@dataclass
class APIRequest:
    pass


@dataclass
class Authenticated:
    access_token: str
