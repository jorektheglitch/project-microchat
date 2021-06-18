from typing import Iterable, Optional

from app.models import User, Message, Attachment, Conference
from app.models import store

from .sse import event_emitter
from .events import MessageReceive
from .events import MessageDelete


@event_emitter(MessageReceive)
async def store_pm(
    from_: int,
    to: int,
    text: str,
    attachments: Iterable[int] = (),
    chat_type: int = 1
):
    m = Message(text=text.strip())
    await m.bind(sender=from_, receiver=to, chat_type=chat_type)
    attachments = [
        Attachment(file=attachment, message=m.id, position=i)
        for i, attachment in enumerate(attachments)
    ]
    return m, await store(*attachments)


async def edit(
    from_: int,
    to: int,
    id: int,
    text: Optional[str] = None,
    attachments: Optional[Iterable[int]] = None,
    chat_type: int = 1
):
    await User(id=from_).update_pm(to, id, text, attachments)


# @event_emitter(MessageDelete)
async def delete(from_: int, to: int, id: int):
    await User(id=from_).delete_pm(to, id)


async def get_pms(
    requester: int,
    interlocutor: int,
    offset: int,
    count: int,
    chat_type
) -> list:
    u = User(id=requester)
    if chat_type == 1:
        message_rows = await u.get_personal_history(
            interlocutor, offset, count
        )
    elif chat_type == 2:
        pass
    msgs = [
        {
            "id": msg.external_id,
            "sender": msg.sender,
            "text": msg.text,
            "sent": msg.time_sent.timestamp(),
            "edit": msg.time_edit.timestamp() if msg.time_edit else None,
            "attachments": msg.attachments
        } for msg in message_rows
    ]
    return msgs


async def create_conference(username, owner, users):
    c = Conference(username=username)
    await c.create(owner, users)


async def overview_pms(user):
    u = User(id=user)
    chat_rows = await u.pm_overview()
    chats = [
        {
            'chat': {
                'id': chat.interlocutor,
                'username': chat.username,
                'chat_type': chat.type
            },
            'message': {
                'sender': chat.sender,
                'text': chat.Message.text,
                'sent': chat.Message.time_sent.timestamp(),
            }
        } for chat in chat_rows
    ]
    return chats


async def overview(user):
    pass
