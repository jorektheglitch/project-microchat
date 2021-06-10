from datetime import (
    datetime as dt,
    timezone as tz
)
from dataclasses import dataclass

from aiohttp.web import Request

from .event_mixin import EventMixin


@dataclass
class MessageReceive(EventMixin):  # OK

    sender: int
    receiver: int
    text: str
    time_sent: int
    time_edit: int
    attachments: list
    chat_type: bool = 1

    __handlers__ = set()

    @classmethod
    async def emit(cls, from_, to, text, attachments, *args, **kwargs):
        sender = kwargs.get('from_', from_)
        receiver = kwargs.get('to', to)
        text = kwargs.get('text', text)
        attachments = kwargs.get('attachments', attachments)
        time_sent = kwargs.get('time_sent', dt.now(tz.utc).timestamp())
        time_edit = kwargs.get('time_edit')
        chat_type = kwargs.get('chat_type', 1)
        return cls(
            sender,
            receiver,
            text,
            time_sent,
            time_edit,
            attachments,
            chat_type
        )


@dataclass
class MessageRequest(EventMixin):

    user_id: int
    chat_id: int
    offset: int
    count: int

    __handlers__ = set()

    @classmethod
    async def emit(cls, request: Request):
        pass


@dataclass
class MessageDelete(EventMixin):

    __handlers__ = set()

    @classmethod
    async def emit(cls, request: Request):
        pass


@dataclass
class ChatCreate(EventMixin):

    chat_id: int
    chat_name: str
    members: tuple

    __handlers__ = set()

    @classmethod
    async def emit(cls, request: Request):
        pass


@dataclass
class ChatsRequest(EventMixin):  # OK

    user_id: int

    __handlers__ = set()

    @classmethod
    async def emit(cls, request: Request):
        pass


@dataclass
class ChatDelete(EventMixin):

    __handlers__ = set()

    @classmethod
    async def emit(cls, request: Request):
        pass
