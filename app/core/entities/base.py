from dataclasses import dataclass, fields
from functools import reduce
from typing import Any, Iterable, Dict, Type, TypeVar, Union


Entity = TypeVar('Entity')
AttributeName = str
AttributesChain = Iterable[AttributeName]
AttributesMap = Dict[str, Union[AttributeName, AttributesChain]]
DefaultsMap = Dict[str, Any]


@dataclass
class BaseEntity:

    @classmethod
    def from_object(
        cls: Type[Entity],
        obj: Any,
        attrmap: AttributesMap = {},
        defaults: DefaultsMap = {},
    ) -> Entity:
        """
        Initialize a instance of dataclass with information from attributes of
        another object.

        Params:
            obj: Any - object which contains information.
            attrmap - map for "rename" attributes to dataclass fields.
            attrchain - chains of attributes names for nested attrs.
            defaults - delault values fo fields.
        """
        info = {}
        for field in fields(cls):
            name = field.name
            if name in defaults:
                value = defaults[name]
            else:
                chain = attrmap.get(name, name)
                if isinstance(chain, str):
                    chain = [chain]
                value = reduce(getattr, chain, initial=obj)
            info[name] = value
        return cls(**info)
