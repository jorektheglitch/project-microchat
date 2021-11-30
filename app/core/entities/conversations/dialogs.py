from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generator, List, Sequence, Union, overload, TYPE_CHECKING
from sqlalchemy.ext import asyncio

from sqlalchemy.sql.expression import and_, not_, select
from sqlalchemy.sql.functions import func

from app.models import models as db
from app.models.bindings import relations_messages, relations_message
from app.models.models import Relation, execute

from app.core.entities.utils import dynamic_attr, BoundProperty
from app.core.entities.message import Message
from .base import Conversation

if TYPE_CHECKING:
    from app.core.entities.user import User


@dataclass
class PersonalMessage(Message):

    dialog: Dialog


class PersonalMessages:

    dialog: Dialog

    def __init__(self, dialog: Dialog):
        self.dialog = dialog

    @overload
    async def __getitem__(self, index: int) -> PersonalMessage:
        ...

    @overload
    async def __getitem__(self, undex: slice) -> List[PersonalMessage]:
        ...

    async def __getitem__(self, index: Union[int, slice]):
        if isinstance(index, slice):
            offset = index.start or 0
            count = index.stop or 100
            reverse = index.step < 0 if index.step else False
            return await self._get_many(offset, count, reverse)
        elif isinstance(index, int):
            return await self._get_one(index)
        else:
            cls = self.__class__
            raise TypeError(f"{cls.__name__} indices must be integers")

    async def _get_many(self, offset: int, count: int, reverse: bool):
        if self.dialog.int_id is not None:
            relations = select(Relation.subject_id, Relation.object_id)\
                .filter(Relation.id == self.dialog.int_id)
        elif self.dialog.ext_id is not None:
            dialog_id = func.row_number().over(
                order_by=Relation.id,
                partition_by=Relation.subject_id
            )
            ext_id = dialog_id.label('ext_id')
            total_relations = select(ext_id, Relation)
            relations = select(
                    total_relations.c.id
                )\
                .filter(
                    total_relations.c.subject_id == self.dialog.user.id,
                    total_relations.c.ext_id == self.dialog.ext_id
                )
        elif self.dialog.username is not None:
            relations = select(Relation.subject_id, Relation.object_id)\
                .select_from(Relation)\
                .join(db.User, db.User.id == Relation.subject_id)\
                .filter(
                    Relation.subject_id == self.dialog.user.id,
                    db.User.username == self.dialog.username
                )
        else:
            raise RuntimeError("Can't resolve relation info")
        binding = relations_message
        order_by = binding.message_id
        reverse = offset < 0
        if reverse:
            offset = ~offset
            ordering = order_by.desc()
        else:
            ordering = order_by.asc()
        message_number = func.row_number().over(order_by=binding.message_id)  # noqa
        external_id = message_number.label('external_id')
        messages = select([
                external_id,
                relations_messages,
                Relation.subject_id.label('sender')
            ])\
            .select_from(relations_messages)\
            .join(Relation, Relation.id == relations_message.relation_id)\
            .filter(
                relations_message.relation_id.in_(relations)
            )\
            .order_by(ordering)\
            .subquery()
        message = messages.c
        query_ordering = message.external_id
        if reverse:
            query_ordering = query_ordering.desc()
        query = select(
                db.Message,
                message.sender,
                message.external_id,
            )\
            .select_from(messages)\
            .join(db.Message, db.Message.id == message.message_id)\
            .filter(not_(db.Message.deleted))\
            .limit(count).offset(offset)\
            .order_by(query_ordering)
        rows = await execute(query)
        return [
            PersonalMessage.from_object(
                row,
                attrmap={
                    "int_id": ["Message", "id"],      # same as row.Message.id
                    "ext_id": "external_id",          # same as row.external_id
                    "text": ["Message", "text"],
                    "time_edit": ["Message", "time_edit"],
                    "time_sent": ["Message", "time_sent"],
                },
                defaults={"dialog": self.dialog}
            )
            for row in rows
        ]

    async def _get_one(self, index: int):
        pass


@dataclass
class Dialog(Conversation):

    name: str = dynamic_attr(default=None)
    surname: str = dynamic_attr(default=None)
    messages = BoundProperty(PersonalMessages)

    async def _get_and_parse(self) -> Dialog:
        dialog_id = func.row_number().over(
            order_by=Relation.id,
            partition_by=Relation.subject_id
        )
        ext_id = dialog_id.label('external_id')
        total_relations = select(ext_id, Relation).subquery()
        relations = select(
                total_relations,
                db.User
            )\
            .select_from(total_relations)\
            .join(db.User, db.User.id == total_relations.c.object_id)
        if self.int_id is not None:
            relations_filter = (total_relations.c.id == self.int_id)
        elif self.ext_id is not None:
            relations_filter = and_(
                total_relations.c.subject_id == self.user.id,
                total_relations.c.external_id == self.ext_id
            )
        elif self.username is not None:
            relations_filter = and_(
                total_relations.c.subject_id == self.user.id,
                db.User.username == self.username
            )
        else:
            raise RuntimeError("Can't resolve relation info")
        relation_query = relations.filter(relations_filter)
        relation_rows = await execute(relation_query)
        relation_info = relation_rows[0]
        interlocutor = relation_info.User
        self.int_id = relation_info.id
        self.ext_id = relation_info.external_id
        self.name = relation_info.name or interlocutor.name
        self.surname = relation_info.surname or interlocutor.surname
        self.username = interlocutor.username
        return self

    def __await__(self) -> Generator[Any, None, Dialog]:
        return self._get_and_parse().__await__()


class Dialogs:

    def __init__(self, user: 'User') -> None:
        self.bound_user = user

    async def _get_and_parse(self):
        ext_id = func.row_number().over(order_by=Relation.id)\
            .label('external_id')
        query = select([Relation, db.User, ext_id])\
            .join(db.User, db.User.id == Relation.object_id)\
            .filter(Relation.subject_id == self.bound_user.id)
        rows = await execute(query)
        return [Dialog(
            int_id=row.Relation.id,
            ext_id=row.external_id,
            name=row.Relation.name or row.User.name,
            surname=row.Relation.surname or row.User.surname,
            username=row.User.username,
            user=self.bound_user
        ) for row in rows]

    def __await__(self) -> Generator[Any, None, Sequence[Dialog]]:
        return self._get_and_parse().__await__()

    def __getitem__(self, index) -> Dialog:
        info = {"user": self.bound_user}
        info.update(dict.fromkeys(("ext_id", "int_id", "username")))
        if isinstance(index, slice):
            cls = self.__class__
            raise TypeError(f"{cls.__name__} object is not slicable")
        elif isinstance(index, int):
            info.update(ext_id=index)
        elif isinstance(index, str):
            info.update(username=index)
        return Dialog(**info)
