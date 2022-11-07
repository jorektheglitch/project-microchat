from typing import Any, Mapping, TypeVar


T = TypeVar("T")


class Config:

    @classmethod
    def from_mapping(  # type: ignore
        cls: type[T], mapping: Mapping[str, Any]
    ) -> T:
        config = cls()
        return config
