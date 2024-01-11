from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    app: ApplicationConfig
    db: DBConfig
    jwt_secret: str


@dataclass(frozen=True)
class DBConfig:
    dbms: str
    host: str
    port: int
    driver: str
    database: str
    username: str
    password: str


@dataclass(frozen=True)
class ApplicationConfig:
    host: str
    port: int
