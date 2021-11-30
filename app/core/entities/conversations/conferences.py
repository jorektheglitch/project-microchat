from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy.sql.expression import select

from app.models import models as db
from app.models.bindings import conferences_users
from app.models.models import execute

from app.core.entities.utils import dynamic_attr, BoundProperty
from app.core.entities.message import Message
from .base import Conversation

if TYPE_CHECKING:
    from app.core.entities.user import User


@dataclass
class ConferenceMessage(Message):

    conference: Conference


class ConferenceMessages:
    pass


class ConferenceUsers:
    pass


@dataclass
class Conference(Conversation):

    title: str = dynamic_attr(default=None)
    users = BoundProperty(ConferenceUsers)
    messages = BoundProperty(ConferenceMessages)


class Conferences:

    def __init__(self, user: 'User') -> None:
        self.user = user

    async def _get_and_parse(self):
        Conf = db.Conference
        query = select(Conf)\
            .select_from(conferences_users)\
            .join(Conf, Conf.id == conferences_users.c.conference)\
            .filter(conferences_users.c.user == self.user.id)
        rows = await execute(query)
        return [
            Conference(
                id=row.Conference.id,
                username=row.Conference.username,
                title=row.Conference.title
            )
            for row in rows
        ]

    def __await__(self):
        return self._get_and_parse().__await__()

    def __getitem__(self, index):
        info = {
            "id": None,
            "username": None
        }
        if isinstance(index, slice):
            cls = self.__class__
            raise TypeError(f"{cls.__name__} object is not slicable")
        elif isinstance(index, int):
            info["id"] = index
        elif isinstance(index, str):
            info["username"] = index
        return Conference(**info)
