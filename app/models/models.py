from __future__ import annotations
import asyncio

from datetime import datetime as dt
import secrets
import logging
from typing import Tuple, Iterable
from typing import Optional, Union

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import MetaData

from sqlalchemy import Column, ForeignKey
from sqlalchemy import Boolean, Integer, Text, DateTime, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql.elements import not_

from sqlalchemy.sql.expression import (
    insert, select, case, func, literal, union, update
)
from sqlalchemy import or_, and_

from .base import Model, metadata, with_session, create_median_function
from .base import CASCADE, RESTRICT
from .bindings import conferences_users, conferences_messages, users_messages
from .bindings import roles_permissions
from .types import sha512


logger = logging.getLogger(__name__)


async def init(db, **options) -> AsyncEngine:
    """
    Инициализация соединения с базой данных, создание таблиц.
    """
    engine = create_async_engine(db, **options)
    metadata.bind = engine
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
        await create_median_function(conn)
        await conn.commit()
    return engine


async def drop(metadata: MetaData) -> None:
    """
    Удаление всех таблиц из базы данных.
    """
    engine = metadata.bind
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.commit()


class Message(Model):
    """
    Модель сообщения в БД.
      id (int) - идентификатор сообщения
      text (str) - текст сообщения
      time_sent (datetime) - время отправки сообщения
      time_edit (datetime) - время последнего редактирования сообщения
      reply_to (int) - ссылка на сообщение, к которому данное сообщение ответ
    """
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    time_sent = Column(DateTime, nullable=False, default=dt.now)
    time_edit = Column(DateTime, nullable=True)
    reply_to = Column(
        Integer,
        ForeignKey(id, onupdate=RESTRICT, ondelete=RESTRICT),
        nullable=True
    )
    deleted = Column(Boolean, nullable=False, default=False)

    # attachments = relationship(
    #    "Attachment",
    #    back_populates="message"
    # )

    @with_session
    async def bind(
        self,
        sender: int,
        receiver: int,
        *,
        session: AsyncSession,
        chat_type: int = 1
    ) -> None:
        session.add(self)
        await session.flush()
        params = {}
        if chat_type == 1:
            binding = users_messages
            params.update(sender=sender, receiver=receiver)
        elif chat_type == 2:
            binding = conferences_messages
            params.update(user=sender, conference=receiver)
        query = binding.insert().values(
            message=self.id,
            **params
        )
        await execute(query, session=session, fetch=False)


class User(Model):
    """
    Модель пользователя в БД.

      id (int) - идентификатор пользователя

      username (str) - никнейм пользователя ()

      name (str) - имя пользователя ()

      surname (str) - фамилия пользователя
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=True)
    surname = Column(Text, nullable=True)
    conferences = relationship(
        "Conference",
        secondary=conferences_users,
        back_populates="users"
    )
    conference_messages = relationship(
        "Message",
        secondary=conferences_messages
    )
    conferences_previews = relationship(
        "Message",
        secondary=conferences_users,
        viewonly=True
    )
    personal_messages = relationship(
        "Message",
        primaryjoin=or_(
            id == users_messages.c.sender,
            id == users_messages.c.receiver,
        ),
        secondary=users_messages
        # primaryjoin=(Message.id == users_messages.c.message),
        # secondary=users_messages,
        # secondaryjoin=or_(
        #    id == users_messages.c.sender,
        #    id == users_messages.c.receiver,
        # )
    )

    @with_session
    async def pm_overview(self, *, session: AsyncSession) -> Tuple:
        def ent_type(value):
            return literal(value).label('type')
        pms = users_messages
        pm = pms.c
        cms = conferences_messages
        cm = cms.c
        interlocutor = case(
                (pm.receiver == self.id, pm.sender),
                else_=pm.receiver
            ).label('interlocutor')
        personal = select(
                interlocutor,
                func.max(pm.message).label('last_message'),
                ent_type(1)
            )\
            .select_from(pms)\
            .join(User, User.id == interlocutor)\
            .filter(
                or_(pm.sender == self.id, pm.receiver == self.id)
            )\
            .group_by('interlocutor')
        personal_overview = select(
                personal.c.interlocutor,
                personal.c.last_message,
                personal.c.type,
                pm.sender,
                User.username
            ).select_from(personal)\
            .join(pms, pm.message == personal.c.last_message)\
            .join(User, User.id == personal.c.interlocutor)
        conference = select(
                cm.conference.label('interlocutor'),
                func.max(cm.message).label('last_message'),
                literal(2).label('type')
            )\
            .select_from(conferences_users)\
            .join(cms, cm.conference == conferences_users.c.conference)\
            .join(Conference, Conference.id == cm.conference)\
            .filter(
                conferences_users.c.user == self.id,
            )\
            .group_by('interlocutor')
        conference_overview = select(
                conference.c.interlocutor,
                conference.c.last_message,
                conference.c.type,
                cm.sender,
                Conference.username
            ).select_from(conference)\
            .join(cms, cm.message == conference.c.last_message)\
            .join(Conference, Conference.id == conference.c.interlocutor)
        conversations = union(
            personal_overview, conference_overview
        ).subquery()
        conv = conversations.c
        query = select(
                Message,
                conversations
            )\
            .select_from(conversations)\
            .join(Message, Message.id == conv.last_message)\
            .order_by(Message.id.desc())
        return await execute(query, session=session)

    @with_session
    async def get_personal_history(
        self,
        other: Union[User, int],
        offset: int,
        limit: int,
        *,
        session: AsyncSession
    ) -> Tuple:
        if isinstance(other, User):
            other = other.id
        binding = users_messages.c
        order_by = Message.id
        reverse = offset < 0
        if reverse:
            offset = ~offset
            ordering = order_by.desc()
        else:
            ordering = order_by.asc()
        message_number = func.row_number().over(order_by=binding.message)
        external_id = message_number.label('external_id')
        messages = select(
                external_id,
                Message,
                users_messages
            )\
            .select_from(users_messages)\
            .join(Message)\
            .filter(
                or_(
                    and_(binding.sender == self.id, binding.receiver == other),
                    and_(binding.sender == other, binding.receiver == self.id),
                )
            )\
            .order_by(ordering)\
            .subquery()
        message = messages.c
        attachments = func.to_json(
            func.ARRAY(
                select(
                    func.json_build_object(
                        literal('id'), File.id,
                        literal('name'), File.name,
                        literal('size'), File.size,
                        literal('type'), File.type
                    ))
                .select_from(Attachment)
                .join(File)
                .filter(Attachment.message == message.id)
                .order_by(Attachment.position)
            )).label('attachments')
        query_ordering = message.external_id
        if reverse:
            query_ordering = query_ordering.desc()
        query = select(
                messages, attachments
            )\
            .select_from(messages)\
            .filter(not_(message.deleted))\
            .limit(limit).offset(offset)\
            .order_by(query_ordering)
        return await execute(query, session=session)

    @with_session
    async def update_pm(
        self,
        other: int,
        message_id: int,
        new_text: str,
        attachments,
        *,
        session: AsyncSession
    ):
        binding = users_messages.c
        id = func.row_number().over(order_by=binding.message).label('id')
        messages = select(
                id,
                Message.id.label('real_id')
            )\
            .select_from(users_messages)\
            .join(Message)\
            .filter(
                or_(
                    and_(binding.sender == self.id, binding.receiver == other),
                    and_(binding.sender == other, binding.receiver == self.id),
                )
            )\
            .subquery()
        query = update(
                Message
            )\
            .values(text=new_text, time_edit=dt.now())\
            .where(
                messages.c.id == message_id,
                messages.c.real_id == Message.id
            )\
            .execution_options(synchronize_session="fetch")
        await execute(query, session=session, fetch=False)

    @with_session
    async def delete_pm(
        self,
        other: int,
        message_id: int,
        *,
        session: AsyncSession
    ):
        binding = users_messages.c
        id = func.row_number().over(order_by=binding.message).label('id')
        messages = select(
                id,
                Message.id.label('real_id')
            )\
            .select_from(users_messages)\
            .join(Message)\
            .filter(
                or_(
                    and_(binding.sender == self.id, binding.receiver == other),
                    and_(binding.sender == other, binding.receiver == self.id),
                )
            )\
            .subquery()
        query = update(
                Message
            )\
            .values(deleted=True)\
            .where(
                messages.c.id == message_id,
                messages.c.real_id == Message.id
            )\
            .execution_options(synchronize_session="fetch")
        await execute(query, session=session, fetch=False)

    @with_session
    async def get_conversation_history(
        self,
        conference: Union[Conference, int],
        offset: int,
        limit: int,
        *,
        session: AsyncSession
    ) -> Tuple:
        binding = conferences_messages.c
        return await execute(
            self.conference_messages.filter(
                binding.conference == conference
            )
            .limit(limit).offset(offset)
            .order_by(Message.time_sent.desc()),
            session=session
        )

    @classmethod
    @with_session
    async def resolve(
        cls,
        username: str,
        *,
        session: AsyncSession
    ) -> Optional[User]:
        lst = await execute(
            cls.filter(User.username == username),
            session=session
        )
        if lst:
            return lst[0]
        return None

    @classmethod
    @with_session
    async def search(
        cls,
        username: str,
        *,
        session: AsyncSession
    ) -> Tuple:
        pattern = '%{}%'.format(username)
        query = cls.filter(cls.username.like(pattern))
        users = await session.execute(query)
        users = tuple(users)
        return users

    @with_session
    async def get_token(self, *, session: AsyncSession) -> str:
        raw_token = secrets.token_bytes(32)
        binding = Token(user=self.id, token=raw_token)
        await binding.store(session=session)
        token = raw_token.hex()
        return token


class Token(Model):
    """
    Модель access токена в БД. Токены используются для аутентификации сессии.
      token (bytes) - токен
      user (int) - ссылка на пользователя, к которому привязан токен
    """
    __tablename__ = "tokens"
    token = Column(LargeBinary, primary_key=True)
    user = Column(
        Integer,
        ForeignKey(User.id, onupdate=RESTRICT, ondelete=CASCADE)
    )

    @classmethod
    @with_session
    async def get_user(cls, token, *, session: AsyncSession) -> User:
        rows = await execute(
            select(User)
            .select_from(cls)
            .join(User)
            .where(
                cls.token == token
            ),
            session=session
        )
        if rows:
            return rows[0][0]


class AuthData(Model):
    """
    Модель аутентификационных данных в БД. Аутентификационные используются
    для проверки пользователя перед выдачей ему токена.
      user (int) - ссылка на пользователя
      method (str) - метод аутентификации
      data (bytes) - данные, необходимые для аутентификации
    """
    __tablename__ = "authentication"
    user = Column(
        Integer,
        ForeignKey(User.id, onupdate=RESTRICT, ondelete=CASCADE),
        primary_key=True
    )
    method = Column(Text, primary_key=True)
    data = Column(LargeBinary)

    @classmethod
    @with_session
    async def get_user(
        cls,
        username,
        method,
        data,
        *,
        session
    ) -> User:
        rows = await execute(
            select(User)
            .select_from(cls)
            .join(User)
            .where(
                cls.method == method,
                cls.data == data,
                User.username == username,
            ),
            session=session
        )
        if rows:
            return rows[0][0]


class File(Model):
    """
    Модель файла в БД.
      id - идентификатор файла
      hash - SHA-512 хеш файла
      size - размер файла (в байтах)
      type - MIME-тип файла
      name - имя файла (используется при вложении файла в сообщение)
    """
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, autoincrement=True)
    hash = Column(sha512)
    size = Column(Integer)
    type = Column(Text)
    name = Column(Text)
    loaded_at = Column(DateTime, nullable=False, default=dt.now)
    loaded_by = Column(
        Integer,
        ForeignKey(User.id)
    )


class Attachment(Model):
    """
    Модель вложений в сообщение в БД.
      file - ссылка на файл
      message - ссылка на сообщение
      position - позиция данного вложения среди прочих вложений
    """
    __tablename__ = "attachments"
    file = Column(
        Integer,
        ForeignKey(File.id, onupdate=RESTRICT, ondelete=RESTRICT),
        primary_key=True
    )
    message = Column(
        Integer,
        ForeignKey(Message.id, onupdate=RESTRICT, ondelete=CASCADE),
        primary_key=True
    )
    position = Column(Integer)

    @classmethod
    @with_session
    async def resolve(cls, message, file, *, session):
        query = select(File)\
            .select_from(cls)\
            .join(File)\
            .filter(
                cls.file == file,
                cls.message == message
            )
        rows = await execute(query, session=session)
        if rows:
            return rows[0]


class Conference(Model):
    """
    """
    __tablename__ = "conferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False, unique=True)
    title = Column(Text)
    users = relationship(
        "User",
        secondary=conferences_users,
        back_populates="conferences"
    )
    messages = relationship("Message", secondary=conferences_messages)

    @with_session
    async def create(self, owner: int, users=(), *, session: AsyncSession):
        session.add(self)
        await session.flush()
        coros = [execute(insert(
            conferences_users,
            user=owner,
            conference=self.id,
            creator=True
        ), commit=False)]
        for user in users:
            query = insert(
                conferences_users,
                user=user,
                conference=self.id,
                creator=False
            )
            coro = execute(query, commit=False)
            coros.append(coro)
        await asyncio.gather(*coros)
        await session.commit()


class Role(Model):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text)
    permissions = relationship(
        "Permission",
        secondary=roles_permissions,
        back_populates="roles"
    )


class Permission(Model):
    __tablename__ = "permissions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text)
    roles = relationship(
        "Role",
        secondary=roles_permissions,
        back_populates="permissions"
    )


@with_session
async def execute(
    query,
    *,
    session: AsyncSession,
    fetch=True,
    commit=True
) -> Optional[Tuple]:
    raw = await session.execute(query)
    if commit:
        await session.commit()
    if fetch:
        return raw.fetchall()


@with_session
async def store(*objects: Iterable[Model], session: AsyncSession):
    session.add_all(objects)
    await session.commit()
    return objects
