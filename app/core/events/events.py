from dataclasses import dataclass

from aiohttp.web import Request

from .event_mixin import EventMixin

from .messages import MessageReceive, MessageRequest, MessageEdit, MessageDelete  # noqa
from .messages import ChatCreate, ChatsRequest, ChatDelete                        # noqa
from .users import NewUser, UserChanged, UserDelete                               # noqa
from .users import UserOnline, UserOffline                                        # noqa


@dataclass
class SSEStart(EventMixin):

    __handlers__ = set()

    def from_request(self, request: Request):
        pass


@dataclass
class SSEEnd(EventMixin):

    __handlers__ = set()

    def from_request(self, request: Request):
        pass


@dataclass
class PollingStart(EventMixin):

    __handlers__ = set()

    def from_request(self, request: Request):
        pass


@dataclass
class PollingRequest(EventMixin):

    __handlers__ = set()

    def from_request(self, request: Request):
        pass


@dataclass
class PollingEnd(EventMixin):

    __handlers__ = set()

    def from_request(self, request: Request):
        pass
