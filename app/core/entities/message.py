from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Union, Optional, TYPE_CHECKING

from app.core.entities.base import BaseEntity

if TYPE_CHECKING:
    from app.core.entities.user import User


@dataclass
class Message(BaseEntity):

    int_id: int
    ext_id: int
    text: Union[str, bytes]  # for futher functionality (encrypted messages)
    time_sent: datetime
    time_edit: datetime
    reply_to: Optional[Message]
    sender: 'User'
