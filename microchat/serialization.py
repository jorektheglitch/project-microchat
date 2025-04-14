"""
Very shitty binary representation for entities.
"""
# TODO: make a good binary format for entities' binary representation.

import io
import json
from dataclasses import is_dataclass
from typing import Any, TypeAlias

from adaptix import P, Retort, dumper, loader

from microchat import entities
from microchat.hashing import DIGEST_SIZE, Hash, Reference, hash_primitive


Entity: TypeAlias = Any  # TODO: precise sumtype for all entities


entities_types = {
    ty.__name__: ty
    for ty in vars(entities).values()
    if is_dataclass(ty) and isinstance(ty, type)
}

marks = {
    hash_primitive(name).raw: type
    for name, type in entities_types.items()
}


def dump_event_ordering(ordering: entities.EventOrdering) -> dict[str, Any]:
    return {
        "others_events": [{"key": reference.key.raw.hex()} for reference in ordering.others_events],
        "own_events": [{"key": reference.key.raw.hex()} for reference in ordering.own_events],
    }


def load_event_ordering(value: dict[str, Any]) -> entities.EventOrdering:
    return entities.EventOrdering(
        others_events=tuple(
            Reference(key=Hash(raw=bytes.fromhex(ref["key"])))
            for ref in value["others_events"]
        ),
        own_events=tuple(
            Reference(key=Hash(raw=bytes.fromhex(ref["key"])))
            for ref in value["own_events"]
        ),
    )


_retort = Retort(recipe=[
    dumper(P[Hash], lambda hash: hash.raw.hex()),
    loader(P[Hash], lambda hex: Hash(raw=bytes.fromhex(hex))),
    dumper(P[entities.EventOrdering], dump_event_ordering),
    loader(P[entities.EventOrdering], load_event_ordering),
])


def dump(entity: Entity, retort=_retort) -> bytes:
    mark = hash_primitive(type(entity).__name__).raw

    with io.BytesIO() as buffer:
        buffer.write(mark)

        with io.TextIOWrapper(buffer, encoding="utf-8", write_through=True) as text_view:
            unparsed = retort.dump(entity, type(entity))
            json.dump(unparsed, text_view)
            dumped = buffer.getvalue()

    return dumped


def load(raw: bytes, retort=_retort) -> Entity:
    with io.BytesIO(raw) as buffer:
        mark = buffer.read(DIGEST_SIZE)

        payload_type = marks.get(mark)
        if payload_type is None:
            raise ValueError(f"Mark {mark.hex().upper()} does not match any known type")

        with io.TextIOWrapper(buffer, encoding="utf-8") as text_view:
            unparsed = json.load(text_view)

    return retort.load(unparsed, payload_type)


if __name__ == "__main__":
    from microchat.entities import TextMessage

    test_entity = TextMessage("amogus")
    dumped = dump(test_entity)
    loaded = load(dumped)
    print()
