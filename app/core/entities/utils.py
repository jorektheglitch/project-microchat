import asyncio
import functools
import warnings
from dataclasses import field


dynamic_attr = functools.partial(field, hash=False, compare=False)


class BoundProperty:

    def __init__(self, cls):
        self.cls = cls

    def __get__(self, obj, objtype=None):
        return self.cls(obj)

    def __set__(self, obj, value):
        raise AttributeError('Attempt to set value to readonly attribute')

    def __set_name__(self, owner, name):
        decriptors = getattr(owner, '__descriptors__', {})
        decriptors[name] = self
        setattr(owner, '__descriptors__', decriptors)


class async_property:

    def __init__(self, getter=None, setter=None, deleter=None):
        self._getter = getter
        self._setter = setter
        self._deleter = deleter

    def getter(self, getter):
        if not asyncio.iscoroutinefunction(getter):
            raise ValueError("Property getter must be a coroutine function")
        if self._getter:
            warnings.warn("Redefinition of a property getter", UserWarning)
        self._getter = getter

    def setter(self, setter):
        if not asyncio.iscoroutinefunction(setter):
            raise ValueError("Property setter must be a coroutine function")
        if self._setter:
            warnings.warn("Redefinition of a property setter", UserWarning)
        self._setter = setter

    def geleter(self, deleter):
        if not asyncio.iscoroutinefunction(deleter):
            raise ValueError("Property deleter must be a coroutine function")
        if self._deleter:
            warnings.warn("Redefinition of a property deleter", UserWarning)
        self._deleter = deleter

    def __set_name__(self, owner, name):
        self.name = name
        decriptors = getattr(owner, '__descriptors__', {})
        decriptors[name] = self
        setattr(owner, '__descriptors__', decriptors)

    async def __get__(self, instance, owner=None):
        return await self._getter(instance)

    async def __set__(self, instance, value):
        if self._setter is None:
            raise AttributeError(f"Attribute {instance}.{self.name} is readonly")  # noqa
        await self._setter(instance)

    async def __delete__(self, instance):
        if self._deleter is None:
            raise AttributeError(f"Attribute {instance}.{self.name} can not be deleted")  # noqa
        await self._deleter(instance)
