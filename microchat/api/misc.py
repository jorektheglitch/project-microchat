from dataclasses import dataclass

from typing import TypedDict


@dataclass
class Disposition:
    offset: int
    count: int


class PermissionsPatch(TypedDict):
    read: bool | None
    send: bool | None
    delete: bool | None
    send_media: bool | None
    send_mediamessage: bool | None
    add_user: bool | None
    pin_message: bool | None
    edit_conference: bool | None
