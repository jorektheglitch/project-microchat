import asyncio
import json
from dataclasses import asdict


class EventMixin:

    __handlers__: set

    def emit(self, *args, **kwargs):
        raise NotImplementedError

    def as_json(self):
        return json.dumps(asdict(self))

    @classmethod
    def add_handler(cls, handler):
        cls.__handlers__.add(handler)

    async def process(self):
        coros = [handler(self) for handler in self.__handlers__]
        await asyncio.gather(*coros, return_exceptions=True)

    def __post_init__(self):
        asyncio.ensure_future(self.process())
