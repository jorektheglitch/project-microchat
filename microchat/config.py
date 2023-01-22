from __future__ import annotations

from dataclasses import dataclass

from typing import Any, Mapping, TypeVar


T = TypeVar("T")


class Config:
    app: ApplicationConfig
    db: DBConfig
    jwt_secret: str

    def __init__(self, jwt_secret: str, db: Mapping[str, str], app: Mapping[str, str | int]) -> None:
        self.jwt_secret = jwt_secret
        self.db = DBConfig(**db)
        self.app = ApplicationConfig(**app)

    @classmethod
    def from_mapping(  # type: ignore
        cls: type[T], mapping: Mapping[str, Any]
    ) -> T:
        config = cls(**mapping)
        return config


@dataclass
class DBConfig:
    dbms: str
    host: str
    port: int
    driver: str
    database: str
    username: str
    password: str


@dataclass
class ApplicationConfig:
    host: str
    port: int
