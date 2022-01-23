"""
Module for binding table's models.
"""

from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy import Integer, Boolean

from .base import Model
from .base import CASCADE, RESTRICT, SET_DEFAULT


# User-Conference binding model
#  This table contain info about conferences which users are member of and
#  roles which was granted to users
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

# User-Conference-Message binding model
#  This table contains a conference's messages
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

relations_messages = Table(
    "relations_messages", Model.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("message_id", Integer, ForeignKey("messages.id")),
    Column("relation_id", Integer, ForeignKey("users_relations.id"))
)
relations_message = relations_messages.c

# User-User-Message binding model
#  This table contains personal messages
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

# Roles-Permissions binding model
#  This table contains info about which permissions have each role
roles_permissions = Table(
    "roles_permissions", Model.metadata,
    Column("role", Integer,
           ForeignKey("roles.id", onupdate=RESTRICT, ondelete=CASCADE),
           primary_key=True),
    Column("permission", Integer,
           ForeignKey("permissions.id", onupdate=RESTRICT, ondelete=RESTRICT),
           primary_key=True)
)
