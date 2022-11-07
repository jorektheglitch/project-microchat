from abc import ABCMeta
from typing import Any, Awaitable, MutableSequence, overload
from typing import Generic, Type, TypeVar
from typing import Tuple, Dict
from typing import get_type_hints


T = TypeVar('T')
Owner = TypeVar('Owner')


class EntityMeta(ABCMeta):
    def __new__(mcls, name: str, bases: Tuple[Type], attrs: Dict[str, Any]):
        annotations = {}
        for base in reversed(bases):
            base_annotations = getattr(base, "__annotations__", {})
            annotations.update(base_annotations)
        annotations.update(attrs.get("__annotations__", {}))
        for attr_name in annotations.keys():
            attrs[attr_name] = attribute()
        cls = super().__new__(mcls, name, bases, attrs)
        return cls


def resolve_typehint(hint: str):
    pass


def is_default_generic(t):
    pass


class BoundMutableSequence(
    Generic[T],
    MutableSequence[Awaitable[T]],
    Awaitable[MutableSequence[T]]
):
    pass


class attribute(Generic[T, Owner]):

    def __init__(self) -> None:
        pass

    def __get__(self, instance: Owner, owner: Type[Owner]) -> T:
        if instance is None:
            return self
        name = self.__name__
        if name not in instance.__dict__:
            raise AttributeError(f"{instance} object have no {name} attribute")
        return instance.__dict__[name]

    def __set__(self, instance: Owner, value: T) -> None:
        if instance is None:
            return
        name = self.__name__
        instance.__dict__[name] = value

    def __delete__(self, instance: Owner) -> None:
        if instance is None:
            return self
        name = self.__name__
        if name not in instance.__dict__:
            raise AttributeError(f"{instance} object have no {name} attribute")
        del instance.__dict__[name]

    def __set_name__(self, owner: Type[Owner], name: str):
        self.__name__ = name
        self.__owner__ = owner

    def __getattr__(self, name: str):
        # annotations = getattr(self.__owner__, "__annotations__", {})
        # attr_type = resolve_typehint(annotations[name])
        annotations = get_type_hints(self.__owner__)
        attr_type = annotations[name]
        if is_default_generic(attr_type):
            pass
        else:
            pass
        if name not in annotations:
            raise AttributeError

    @overload
    def __getitem__(self, index: slice): ...
    @overload
    def __getitem__(self, index: Any): ...
    def __getitem__(self, index):  # noqa
        pass


if __name__ == "__main__":
    import asyncio

    @asyncio.coroutine
    def t(n=1):
        yield from asyncio.sleep(0.0000000000000001)
        if n < 0:
            raise RuntimeError("Shit happens")
        # await t_(n-1)
        yield from t(n-1)

    async def t_(n):
        return await t(n)

    loop = asyncio.get_event_loop()
    coro = t()
    loop.run_until_complete(coro)
