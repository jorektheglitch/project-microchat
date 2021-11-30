from __future__ import annotations
from dataclasses import dataclass

from app.core.entities.conversations.dialogs import Dialogs
from app.core.entities.conversations.conferences import Conferences
from app.core.entities.base import BaseEntity
from app.core.entities.utils import dynamic_attr, BoundProperty


@dataclass
class User(BaseEntity):

    id: int
    username: str = dynamic_attr(default=None)
    name: str = dynamic_attr(default=None)
    surname: str = dynamic_attr(default=None)
    dialogs = BoundProperty(Dialogs)
    conferences = BoundProperty(Conferences)
