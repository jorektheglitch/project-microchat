from __future__ import annotations

import asyncio
import secrets
import logging
from datetime import datetime as dt
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
    select, update, union, func, case, literal
)
from sqlalchemy import or_, and_

from .base import Model, metadata, with_session, create_median_function
from .base import CASCADE, RESTRICT
from .bindings import conferences_users, conferences_messages, users_messages
from .bindings import roles_permissions
from .types import sha512


logger = logging.getLogger(__name__)


async def init(db: str, **options) -> AsyncEngine:
    """
    Initialize connection to DB, creating tables
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
    Drop all tables from DB.
    """

    engine = metadata.bind
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)
        await conn.commit()


class Message(Model):
    """
    Message model for DB.

      id (int) - message's internal identifier

      text (str) - message's text

      time_sent (datetime) - message's send time (UTC)

      time_edit (datetime) - message's last edit time (UTC)

      reply_to (int) - link to message which replied to
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

    attachments = relationship(
        "Attachment",
        foreign_keys="Attachment.message_id",
        lazy="selectin"
    )

    @with_session
    async def bind(
        self,
        sender: int,
        receiver: int,
        *,
        session: AsyncSession,
        chat_type: int = 1
    ) -> None:
        """
        Binds a message to it's sender and receiver.
        """

        session.add(self)
        await session.flush()
        params = {}
        if chat_type == 1:
            binding = users_messages
            params.update(sender=sender, receiver=receiver)
        elif chat_type == 2:
            binding = conferences_messages
            params.update(user=sender, conference=receiver)
        await execute(
            binding.insert().values(message=self.id, **params),
            session=session,
            fetch=False, commit=False
        )
        message_number = func.row_number().over(order_by=binding.c.message)
        messages = select(
                message_number.label('external_id'),
                Message
            )\
            .select_from(users_messages)\
            .join(Message)\
            .filter(
                or_(
                    and_(binding.c.sender == sender, binding.c.receiver == receiver),  # noqa
                    and_(binding.c.sender == receiver, binding.c.receiver == sender),  # noqa
                )
            )\
            .order_by(Message.id)\
            .subquery()
        external_id_row = await execute(
            select(messages.c.external_id).where(messages.c.id == self.id),
            session=session,
            commit=False
        )
        external_id = external_id_row[0].external_id
        await session.commit()
        return external_id


class User(Model):
    """
    User model for DB.

      id (int) - user's internal identifier

      username (str) -

      name (str) - user's name (visible in profile)

      surname (str) - user's surname (visible in profile)
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
        """
        Gets a list of user's conversations with it's last messages.
        """

        def ent_type(value):
            return literal(value).label('type')
        pms = select(
                users_messages
            )\
            .select_from(users_messages)\
            .join(Message, Message.id == users_messages.c.message)\
            .where(not_(Message.deleted))\
            .subquery()
        pm = pms.c
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
                User.username,
                personal.c.interlocutor,
                personal.c.last_message,
                pm.sender,
                personal.c.type,
            ).select_from(personal)\
            .join(pms, pm.message == personal.c.last_message)\
            .join(User, User.id == personal.c.interlocutor)
        last_messages = select(
                func.last_value(conferences_messages.c.message).over(
                    partition_by=conferences_messages.c.conference,
                    order_by=conferences_messages.c.message
                ).label('last_message'),
                func.last_value(conferences_messages.c.sender).over(
                    partition_by=conferences_messages.c.conference,
                    order_by=conferences_messages.c.message
                ).label('sender'),
                conferences_messages.c.conference
            )\
            .select_from(conferences_messages)\
            .subquery()
        confs_messages = select(
                last_messages
            )\
            .join(Message, Message.id == last_messages.c.last_message)\
            .filter(not_(Message.deleted))\
            .subquery()
        confs_overview = select(
                Conference.username,
                Conference.id.label('interlocutor'),
                confs_messages.c.last_message,
                confs_messages.c.sender,
                literal(2).label('type')
            )\
            .select_from(conferences_users)\
            .outerjoin(confs_messages, confs_messages.c.conference == conferences_users.c.conference)\
            .join(Conference, Conference.id == conferences_users.c.conference)\
            .filter(conferences_users.c.user == self.id)
        conversations = union(
            personal_overview, confs_overview
        ).subquery()
        conv = conversations.c
        query = select(
                Message,
                conversations
            )\
            .select_from(conversations)\
            .outerjoin(Message, Message.id == conv.last_message)\
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
        """
        Gets a personal conversation history.
        """

        if isinstance(other, User):
            other = other.id
        binding = users_messages.c
        order_by = binding.message
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
                users_messages
            )\
            .select_from(users_messages)\
            .filter(
                or_(
                    and_(binding.sender == self.id, binding.receiver == other),
                    and_(binding.sender == other, binding.receiver == self.id),
                )
            )\
            .order_by(ordering)\
            .subquery()
        message = messages.c
        query_ordering = message.external_id
        if reverse:
            query_ordering = query_ordering.desc()
        query = select(
                Message,
                message.sender,
                message.external_id,
            )\
            .select_from(messages)\
            .join(Message, Message.id == message.message)\
            .filter(not_(Message.deleted))\
            .limit(limit).offset(offset)\
            .order_by(query_ordering)
        return await execute(query, session=session)

    @with_session
    async def update_pm(
        self,
        other: int,
        message_id: int,
        new_text: str,
        attachments: Optional[Iterable[int]] = None,
        *,
        session: AsyncSession
    ):
        """
        Updates a personal message.
        """

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
        """
        Deletes a personal message.
        """

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
        """
        Gets a user's ID from it's username.
        """

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
        """
        Creates a access auth token for user.
        """

        raw_token = secrets.token_bytes(32)
        binding = Token(user=self.id, token=raw_token)
        await binding.store(session=session)
        token = raw_token.hex()
        return token


class Token(Model):
    """
    Access token model for DB. Tokens is used for authenticate API requests.

      token (bytes) -

      user (int) - link to user which owns this token
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
        """
        Gets user which owns this token.
        """

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
    Authentication data model for DB. Authentication data is used for check
    user before grant access token to it.

      user (int) - link to user

      method (str) - authentication method

      data (bytes) - data for authentication performing
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
        username: str,
        method: str,
        data: bytes,
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
    File model for DB.

      id - file's internal identifier

      hash - file's SHA-512 hash

      size - size of file

      type - file's MIME-type

      name - file name (for attaching file to message)
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

    attached = relationship(
        'Attachment',
        foreign_keys='Attachment.file_id',
        back_populates='file'
    )


class Attachment(Model):
    """
    Message's attachment model for DB.

      file - link to File row

      message - link to message

      position - attachments's position in message
    """

    __tablename__ = "attachments"

    file_id = Column(
        "file",
        Integer,
        ForeignKey(File.id, onupdate=RESTRICT, ondelete=RESTRICT),
        primary_key=True
    )
    message_id = Column(
        "message",
        Integer,
        ForeignKey(Message.id, onupdate=RESTRICT, ondelete=CASCADE),
        primary_key=True
    )
    position = Column(Integer)

    file = relationship(File, back_populates='attached', lazy='joined')

    @classmethod
    @with_session
    async def resolve(cls, message, file, *, session):
        """
        Gets a bound file info.
        """
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
    Conference model for DB.

      id (int) - conference's internal identifier

      username (str) -

      title (str) - conferece's visible name
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
    async def create(
        self,
        owner: int,
        users: Iterable[Union[User, int]] = (),
        *,
        session: AsyncSession
    ):
        """
        Creates a conference with selected users.
        """
        session.add(self)
        await session.flush()
        members = [conferences_users.insert().values(user=owner, conference=self.id, creator=True)]  # noqa
        members.extend(
            conferences_users.insert().values(user=user, conference=self.id, creator=False)  # noqa
            for user in users
        )
        coros = [execute(query, session=session, fetch=False) for query in members]  # noqa
        await asyncio.gather(*coros)
        # await session.add_all(members)
        await session.commit()


class Role(Model):
    """
    User's role model for DB.

      id (int) - role's internal identifier
      title (str) - role's visible title
    """

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text)
    permissions = relationship(
        "Permission",
        secondary=roles_permissions,
        back_populates="roles"
    )


class Permission(Model):
    """
    Role's permission table for DB.

      id (int) - permission's internal identifier
      title (str) - permission's visible title
    """

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
    """
    Executes given query. Fetch results and commits changes if otherwise
    don't specified.
    """

    raw = await session.execute(query)
    if commit:
        await session.commit()
    if fetch:
        return raw.fetchall()


@with_session
async def store(*objects: Iterable[Model], session: AsyncSession):
    """
    Adds all given object to DB and commits changes.
    """

    session.add_all(objects)
    await session.commit()
    return objects
