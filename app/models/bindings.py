from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Integer, Boolean

from .base import Model
from .base import CASCADE, RESTRICT, SET_DEFAULT


conferences_users = Table(
    "conferences_users", Model.metadata,
    Column("user", Integer,
           ForeignKey("users.id", onupdate=RESTRICT, ondelete=RESTRICT),
           primary_key=True),
    Column("conference", Integer,
           ForeignKey("conferences.id", onupdate=RESTRICT, ondelete=CASCADE),
           primary_key=True),
    Column("role", Integer,
           ForeignKey("roles.id", onupdate=RESTRICT, ondelete=SET_DEFAULT),
           server_default="1"),
    Column("last_readed", Integer,
           ForeignKey("messages.id", onupdate=RESTRICT)),
    Column("creator", Boolean)
)

conferences_messages = Table(
    "conferences_messages", Model.metadata,
    Column("message", Integer,
           ForeignKey("messages.id", onupdate=RESTRICT, ondelete=CASCADE),
           primary_key=True, unique=True),
    Column("sender", Integer,
           ForeignKey("users.id", onupdate=RESTRICT),
           primary_key=True),
    Column("conference", Integer,
           ForeignKey("conferences.id", onupdate=RESTRICT, ondelete=CASCADE),
           primary_key=True)
)

users_messages = Table(
    "personal_messages", Model.metadata,
    Column("message", Integer,
           ForeignKey("messages.id", onupdate=RESTRICT, ondelete=CASCADE),
           primary_key=True, unique=True),
    Column("sender", Integer,
           ForeignKey("users.id", onupdate=RESTRICT),
           primary_key=True),
    Column("receiver", Integer,
           ForeignKey("users.id", onupdate=RESTRICT),
           primary_key=True)
)

roles_permissions = Table(
    "roles_permissions", Model.metadata,
    Column("role", Integer,
           ForeignKey("roles.id", onupdate=RESTRICT, ondelete=CASCADE),
           primary_key=True),
    Column("permission", Integer,
           ForeignKey("permissions.id", onupdate=RESTRICT, ondelete=RESTRICT),
           primary_key=True)
)
