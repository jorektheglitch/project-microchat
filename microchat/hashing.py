from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence, Set
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime as dt
from functools import reduce
from hashlib import sha3_256
from operator import xor
from typing import Any, Generic, Self, TypeAlias, TypeVar


DIGEST_SIZE = sha3_256().digest_size


@dataclass(frozen=True)
class Hash:
    raw: bytes

    def __post_init__(self) -> None:
        if (digest_len := len(self.raw)) != DIGEST_SIZE:
            raise ValueError(f"Hash must be exactly {DIGEST_SIZE} bytes long, but got {digest_len} bytes.")

    def __hash__(self) -> int:
        return hash(self.raw)


NULL_HASH = Hash(b"\x00"*DIGEST_SIZE)


@dataclass(frozen=True)
class HashableItem(ABC):
    @property
    @abstractmethod
    def hash(self) -> Hash:
        raise NotImplementedError(f"'hash' property is not implemented on {type(self).__name__}")

    def reference(self) -> Reference[Self]:
        return Reference(self.hash)


Target = TypeVar("Target", bound=HashableItem | None, covariant=True)
ExtTarget = TypeVar("ExtTarget", covariant=True)


@dataclass(frozen=True)
class Reference(HashableItem, Generic[Target]):
    key: Hash

    @property
    def hash(self) -> Hash:
        return self.key

    def __hash__(self) -> int:
        return int.from_bytes(self.key.raw, "big")


References: TypeAlias = tuple[Reference[Target], ...]


@dataclass(frozen=True)
class ExternalReference(HashableItem, Generic[ExtTarget]):
    key: Hash

    @property
    def hash(self) -> Hash:
        return self.key


def _hashing_function(data: bytes) -> Hash:
    hasher = sha3_256()
    hasher.update(data)
    return Hash(hasher.digest())


def hash_primitive(primitive: int | str | bytes | dt | None) -> Hash:
    if primitive is None:
        return NULL_HASH
    match primitive:
        case int():
            byte_length = (primitive.bit_length() + 7) // 8
            conversed = primitive.to_bytes(byte_length, byteorder='big', signed=True)
        case str():
            conversed = primitive.encode(encoding='utf-8')
        case bytes():
            conversed = primitive
        case dt():
            conversed = primitive.isoformat(timespec='milliseconds').encode(encoding='utf-8')
        case unsupported:
            raise TypeError(f"Cant hash a {type(unsupported)}")
    return _hashing_function(conversed)


def hash_sequence(sequence: Sequence[Hash]) -> Hash:
    hashes_seq = b"".join(item.raw for item in sequence)
    if not hashes_seq:
        raise RuntimeError("Can't hash empty sequence")
    return hash_primitive(hashes_seq)


def hash_set(hashes: Set[Hash]) -> Hash:
    """
    Like a sequence hash, but don't care about items ordering (done via using XOR).
    """
    hashes = set(hashes)
    if not hashes:
        raise RuntimeError("Can't hash empty set")
    first, *rest = hashes
    if not rest:
        return first
    combined = bytes(reduce(xor, nth_bytes) for nth_bytes in zip(*hashes))
    return Hash(combined)


def hash_any(obj: Any) -> Hash:
    if is_dataclass(obj) and not isinstance(obj, HashableItem):
        return hash_dataclass(obj)

    match obj:
        case int() | str() | bytes() | dt() | None as primitive:
            hash = hash_primitive(primitive)
        case HashableItem():
            hash = obj.hash
        case Sequence():
            hashes = tuple(hash_any(item) for item in obj)
            hash = hash_sequence(hashes)
        case unsupported:
            raise TypeError(f"Can not hash a {type(unsupported)}")

    return hash


def hash_dataclass(obj: Any) -> Hash:
    if not is_dataclass(obj):
        raise TypeError(f"Can't hash {type(obj).__name__} as dataclass")
    if isinstance(obj, type):
        raise TypeError("Can't hash type as dataclass")
    obj_fields = fields(obj)
    hashes: tuple[Hash, ...] = tuple(hash_any(getattr(obj, field.name)) for field in obj_fields)  # type: ignore
    return hash_sequence(hashes)
