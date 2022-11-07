from __future__ import annotations

import logging
from datetime import datetime as dt

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from sqlalchemy import Column, ForeignKey
from sqlalchemy import Boolean, Integer, Text, DateTime, LargeBinary
from sqlalchemy import CheckConstraint, ForeignKeyConstraint
from sqlalchemy import and_
from sqlalchemy.orm import relationship

from .base import Model
from .base import CASCADE, RESTRICT
from .types import sha512


logger = logging.getLogger(__name__)


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


class EntityType(Model):

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, unique=True)


class Entity(Model):

    __tablename__ = "enities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(Integer, ForeignKey(EntityType.id, ondelete=RESTRICT))
    alias = Column(nullable=True, unique=True)


class User(Model):
    """
    User model for DB.

      id (int) - user's internal identifier

      username (str) -

      name (str) - user's name (visible in profile)

      surname (str) - user's surname (visible in profile)
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    type = Column(Integer, default=0)
    name = Column(Text, nullable=True)
    surname = Column(Text, nullable=True)

    __table_args__ = [
        ForeignKeyConstraint(
            (id, type),
            (Entity.id, Entity.type)
        ),
        CheckConstraint(type == 0)
    ]


class Bot(Model):

    __tablename__ = "bots"

    id = Column(Integer, primary_key=True)
    type = Column(Integer, default=1)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)

    __table_args__ = [
        ForeignKeyConstraint(
            (id, type),
            (Entity.id, Entity.type)
        ),
        CheckConstraint(type == 1)
    ]


class Conference(Model):
    """
    Conference model for DB.

      id (int) - conference's internal identifier

      username (str) -

      title (str) - conferece's visible name
    """

    __tablename__ = "conferences"

    id = Column(Integer, primary_key=True)
    type = Column(Integer, default=2)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)

    __table_args__ = [
        ForeignKeyConstraint(
            (id, type),
            (Entity.id, Entity.type)
        ),
        CheckConstraint(type == 2)
    ]


class Relationship(Model):

    __tablename__ = "users_relations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    backward = Column(Integer, ForeignKey(id))
    entity = Column(Integer)
    entity_type = Column(Integer)
    related = Column(Integer)
    related_type = Column(Integer)
    name = Column(Text)
    surname = Column(Text)

    __table_args__ = [
        ForeignKeyConstraint(
            (entity, entity_type),
            (Entity.id, Entity.type)
        ),
        ForeignKeyConstraint(
            (related, related_type),
            (Entity.id, Entity.type)
        ),
        CheckConstraint(
            and_(entity_type != 2, related_type != 2)
        )
    ]


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


class Permission(Model):
    """
    Role's permission table for DB.

      id (int) - permission's internal identifier
      title (str) - permission's visible title
    """

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text)
