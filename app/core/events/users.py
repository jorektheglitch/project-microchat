from dataclasses import dataclass

from aiohttp.web import Request

from .event_mixin import EventMixin


@dataclass
class NewUser(EventMixin):  # OK

    __handlers__ = set()

    @classmethod
    async def from_request(cls, request: Request):
        pass


@dataclass
class UserChanged(EventMixin):  # OK

    __handlers__ = set()

    @classmethod
    async def from_request(cls, request: Request):
        pass


@dataclass
class UserDelete(EventMixin):

    __handlers__ = set()

    @classmethod
    async def from_request(cls, request: Request):
        pass


@dataclass
class UserOnline(EventMixin):

    __handlers__ = set()

    @classmethod
    async def from_request(cls, request: Request):
        pass


@dataclass
class UserOffline(EventMixin):

    __handlers__ = set()

    @classmethod
    async def from_request(cls, request: Request):
        pass
