"""
Module for model's bases - useful functions, constants and Model base class.
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData


metadata = MetaData()
DeclarativeBase = declarative_base(metadata=metadata)

CASCADE = "CASCADE"
RESTRICT = "RESTRICT"
SET_DEFAULT = "SET DEFAULT"
SET_NULL = "SET NULL"


class Model(DeclarativeBase):
    """
    Base class for DB models.
    """

    __abstract__ = True
