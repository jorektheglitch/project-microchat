"""
Module with functions for getting analytics about users, messages, etc
"""

from app.models.base import with_session
from sqlalchemy.sql.expression import select
from sqlalchemy.sql.functions import func

from .bindings import users_messages, conferences_messages
from .models import User, Message, Conference, execute


@with_session
async def users_stats(*, session):
    pms = users_messages
    pm = pms.c
    cms = conferences_messages
    cm = cms.c
    sended_pms = select(
            pm.sender, func.count().label('sended')
        ).select_from(
            pms
        ).group_by(
            pm.sender
        ).order_by(
            pm.sender
        ).subquery()
    sended_pm = sended_pms.c
    receved_pms = select(
            pm.receiver, func.count().label('received')
        ).select_from(
            pms
        ).group_by(
            pm.receiver
        ).order_by(
            pm.receiver
        ).subquery()
    received_pm = receved_pms.c
    personal_messages = select(
            User,
            sended_pms.c.sended,
            receved_pms.c.received
        )\
        .select_from(User)\
        .join(sended_pms, User.id == sended_pm.sender)\
        .join(receved_pms, User.id == received_pm.receiver)
    general_messages = select(
        func.avg(personal_messages.c.sended).label("sended_avg"),
        func.median(personal_messages.c.sended).label("sended_med"),
        func.avg(personal_messages.c.received).label("received_avg"),
        func.median(personal_messages.c.received).label("received_med"),
    ).select_from(personal_messages)
    exact = await execute(personal_messages, session=session)
    generalized = await execute(general_messages, session=session)
    return {
        "exact": exact,
        "general": generalized[0],
    }


@with_session
async def messages_stats():
    Message


@with_session
async def conferences_stats():
    Conference
