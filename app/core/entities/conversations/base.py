from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.core.entities.base import BaseEntity

if TYPE_CHECKING:
    from app.core.entities.user import User


@dataclass
class Conversation(BaseEntity):

    user: 'User'   # what user's conversation is
    ext_id: int    # external id
    int_id: int    # DB id
    username: str
